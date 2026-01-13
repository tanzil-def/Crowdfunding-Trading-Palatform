import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.db import transaction, models
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from rest_framework.exceptions import PermissionDenied

from .models import (
    Project, ProjectImage, Favorite, ProjectComparison,
    RestrictedAccessRequest, ProjectAuditLog
)
from apps.users.models import User
from apps.investments.models import Investment


# ==================== VALIDATION SERVICES ====================

def validate_project_submission(project: Project) -> None:
    """
    Validate project before submission
    
    SRS: A project cannot be submitted unless required fields are completed
    """
    required_fields = {
        'title': 'Title is required',
        'short_description': 'Short description is required',
        'description': 'Description is required',
        'category': 'Category is required',
        'total_project_value': 'Total project value is required',
        'total_shares': 'Total shares is required',
        'duration_days': 'Project duration is required',
    }
    
    for field, error_message in required_fields.items():
        value = getattr(project, field)
        if not value:
            raise ValidationError({field: error_message})
    
    # Validate financials
    if project.total_project_value <= Decimal('0'):
        raise ValidationError({'total_project_value': 'Total project value must be positive'})
    
    if project.total_shares <= 0:
        raise ValidationError({'total_shares': 'Total shares must be positive'})
    
    if project.duration_days < 30:
        raise ValidationError({'duration_days': 'Minimum project duration is 30 days'})


def validate_media_file(file, media_type: str) -> None:
    """
    Validate uploaded media files
    
    SRS: Uploaded media must follow configured size and format limits
    """
    # File size validation
    max_size_mb = {
        'image': 5,  # 5MB for images
        '3d_model': 50,  # 50MB for 3D models
        'document': 10  # 10MB for documents
    }
    
    max_size_bytes = max_size_mb.get(media_type, 5) * 1024 * 1024
    if file.size > max_size_bytes:
        raise ValidationError(f"File size exceeds maximum limit of {max_size_mb[media_type]}MB")
    
    # Format validation
    if media_type == 'image':
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError(f"Image must be one of: {', '.join(allowed_extensions)}")
    
    elif media_type == '3d_model':
        allowed_extensions = ['.glb', '.gltf', '.obj']
        if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError(f"3D model must be one of: {', '.join(allowed_extensions)}")


# ==================== PROJECT SERVICES ====================

@transaction.atomic
def create_project(
    user: User,
    title: str,
    short_description: str,
    description: str,
    category: str,
    total_project_value: Decimal,
    total_shares: int,
    duration_days: int,
    **kwargs
) -> Project:
    """
    Create a new project with validation
    
    SRS: Developers create projects and submit for approval
    """
    # Validate user is a developer
    if not user.is_developer:
        raise PermissionDenied("Only developers can create projects")
    
    # Create project
    project = Project.objects.create(
        developer=user,
        title=title,
        short_description=short_description,
        description=description,
        category=category,
        total_project_value=total_project_value,
        total_shares=total_shares,
        duration_days=duration_days,
        **{k: v for k, v in kwargs.items() if hasattr(Project, k)}
    )
    
    # Create audit log
    create_audit_log(
        project=project,
        actor=user,
        action_type='CREATED',
        description=f"Project '{title}' created"
    )
    
    return project


@transaction.atomic
def submit_project_for_review(project: Project, user: User) -> Project:
    """
    Submit project for admin review
    
    SRS: Developers submit projects for admin review
    """
    if project.developer != user:
        raise PermissionDenied("Only the project developer can submit for review")
    
    if project.status != Project.Status.DRAFT:
        raise ValidationError("Only draft projects can be submitted for review")
    
    # Validate required fields
    validate_project_submission(project)
    
    # Update project status
    project.status = Project.Status.PENDING_REVIEW
    project.submitted_at = timezone.now()
    project.save()
    
    # Create audit log
    create_audit_log(
        project=project,
        actor=user,
        action_type='SUBMITTED',
        description=f"Project '{project.title}' submitted for review"
    )
    
    # Create notification for admins
    from apps.notifications.services import create_notification
    create_notification(
        user=None,  # Will send to all admins
        notification_type='PROJECT_SUBMITTED',
        title='New Project Submission',
        message=f"Project '{project.title}' has been submitted for review",
        related_object=project
    )
    
    return project


@transaction.atomic
def review_project(
    project: Project,
    reviewer: User,
    action: str,
    notes: str = ''
) -> Project:
    """
    Admin review of project
    
    SRS: Admins approve, reject, or request changes
    """
    if not reviewer.is_admin:
        raise PermissionDenied("Only admins can review projects")
    
    if project.status != Project.Status.PENDING_REVIEW:
        raise ValidationError("Project is not in pending review status")
    
    if action == 'approve':
        project.status = Project.Status.APPROVED
        project.start_date = timezone.now()
        if project.duration_days:
            project.end_date = project.start_date + timedelta(days=project.duration_days)
        action_type = 'APPROVED'
        notification_type = 'PROJECT_APPROVED'
    
    elif action == 'reject':
        project.status = Project.Status.REJECTED
        action_type = 'REJECTED'
        notification_type = 'PROJECT_REJECTED'
    
    elif action == 'request_changes':
        project.status = Project.Status.NEEDS_CHANGES
        action_type = 'CHANGES_REQUESTED'
        notification_type = 'PROJECT_NEEDS_CHANGES'
    
    else:
        raise ValidationError("Invalid action")
    
    project.reviewed_at = timezone.now()
    project.reviewed_by = reviewer
    project.review_notes = notes
    project.save()
    
    # Create audit log
    create_audit_log(
        project=project,
        actor=reviewer,
        action_type=action_type,
        description=f"Project '{project.title}' {action}",
        metadata={'review_notes': notes}
    )
    
    # Create notification for developer
    from apps.notifications.services import create_notification
    create_notification(
        user=project.developer,
        notification_type=notification_type,
        title=f'Project {action.capitalize()}',
        message=f"Your project '{project.title}' has been {action}",
        related_object=project
    )
    
    return project


@transaction.atomic
def update_project_shares(
    project: Project,
    shares_to_sell: int
) -> Project:
    """
    Atomically update shares sold (SRS: Prevent overselling)
    
    Uses database-level locking to ensure consistency
    """
    if shares_to_sell <= 0:
        raise ValidationError("Shares to sell must be positive")
    
    with transaction.atomic():
        # Lock the project row for update
        locked_project = Project.objects.select_for_update().get(id=project.id)
        
        # Check available shares
        if locked_project.remaining_shares < shares_to_sell:
            raise ValidationError(
                f"Not enough shares available. "
                f"Requested: {shares_to_sell}, "
                f"Available: {locked_project.remaining_shares}"
            )
        
        # Update shares sold
        locked_project.shares_sold = models.F('shares_sold') + shares_to_sell
        locked_project.save()
    
    # Refresh and return updated project
    project.refresh_from_db()
    return project


# ==================== FAVORITES & COMPARISON ====================

def add_to_favorites(user: User, project: Project, notes: str = '') -> Favorite:
    """
    Add project to user's favorites
    
    SRS: Investors can favorite projects
    """
    if not user.is_investor:
        raise PermissionDenied("Only investors can favorite projects")
    
    if project.status != Project.Status.APPROVED:
        raise ValidationError("Only approved projects can be favorited")
    
    favorite, created = Favorite.objects.get_or_create(
        user=user,
        project=project,
        defaults={'notes': notes}
    )
    
    if not created:
        raise ValidationError("Project is already in favorites")
    
    return favorite


def create_project_comparison(
    user: User,
    project_ids: List[uuid.UUID],
    name: str = '',
    notes: str = ''
) -> ProjectComparison:
    """
    Create project comparison
    
    SRS: Compare 2-4 projects side by side
    """
    if len(project_ids) < 2:
        raise ValidationError("Select at least 2 projects to compare")
    
    if len(project_ids) > 4:
        raise ValidationError("Cannot compare more than 4 projects")
    
    # Get approved projects
    projects = Project.objects.filter(
        id__in=project_ids,
        status=Project.Status.APPROVED
    )
    
    if projects.count() != len(project_ids):
        raise ValidationError("Some projects are not available for comparison")
    
    # Create comparison
    comparison = ProjectComparison.objects.create(
        user=user,
        name=name,
        notes=notes
    )
    comparison.projects.set(projects)
    
    return comparison


def get_comparison_data(comparison: ProjectComparison) -> Dict[str, Any]:
    """
    Get normalized comparison data for side-by-side view
    
    SRS: Comparator presented as side-by-side table
    """
    projects = comparison.projects.all()
    
    # Calculate normalized values for comparison
    per_share_prices = [p.per_share_price for p in projects]
    funding_progress = [p.funding_progress for p in projects]
    total_values = [float(p.total_project_value) for p in projects]
    
    def normalize(value_list, value):
        if not value_list:
            return 0
        min_val = min(value_list)
        max_val = max(value_list)
        if max_val == min_val:
            return 1
        return (value - min_val) / (max_val - min_val)
    
    comparison_data = []
    for project in projects:
        project_data = {
            'id': str(project.id),
            'title': project.title,
            'category': project.get_category_display(),
            'developer': {
                'id': str(project.developer.id),
                'name': project.developer.full_name,
                'email': project.developer.email
            },
            'financials': {
                'total_value': float(project.total_project_value),
                'total_shares': project.total_shares,
                'shares_sold': project.shares_sold,
                'remaining_shares': project.remaining_shares,
                'per_share_price': float(project.per_share_price),
                'funding_secured': float(project.funding_secured),
                'funding_progress': project.funding_progress
            },
            'normalized': {
                'per_share_price': normalize(per_share_prices, float(project.per_share_price)),
                'funding_progress': normalize(funding_progress, project.funding_progress),
                'total_value': normalize(total_values, float(project.total_project_value))
            },
            'timeline': {
                'duration_days': project.duration_days,
                'start_date': project.start_date,
                'end_date': project.end_date,
                'days_remaining': project.days_remaining
            }
        }
        comparison_data.append(project_data)
    
    return {
        'comparison_id': str(comparison.id),
        'name': comparison.name,
        'notes': comparison.notes,
        'projects': comparison_data,
        'created_at': comparison.created_at,
        'updated_at': comparison.updated_at
    }


# ==================== RESTRICTED ACCESS SERVICES ====================

@transaction.atomic
def request_restricted_access(
    investor: User,
    project: Project,
    purpose: str = '',
    requested_fields: List[str] = None
) -> RestrictedAccessRequest:
    """
    Request access to restricted project data
    
    SRS: Verified investors can request access to restricted project details
    """
    if not investor.is_investor:
        raise PermissionDenied("Only investors can request access to restricted data")
    
    if not investor.is_verified:
        raise PermissionDenied("Email verification required for access requests")
    
    if project.status != Project.Status.APPROVED:
        raise ValidationError("Only approved projects have restricted data")
    
    # Check for existing request
    if RestrictedAccessRequest.objects.filter(
        investor=investor,
        project=project
    ).exists():
        raise ValidationError("You have already requested access to this project")
    
    # Create access request
    access_request = RestrictedAccessRequest.objects.create(
        investor=investor,
        project=project,
        purpose=purpose,
        requested_fields=requested_fields or []
    )
    
    # Create audit log
    create_audit_log(
        project=project,
        actor=investor,
        action_type='ACCESS_REQUESTED',
        description=f"Access requested for project '{project.title}'",
        metadata={'investor_email': investor.email}
    )
    
    # Create notification for admins
    from apps.notifications.services import create_notification
    create_notification(
        user=None,  # Will send to all admins
        notification_type='ACCESS_REQUESTED',
        title='New Access Request',
        message=f"Investor {investor.email} requested access to '{project.title}'",
        related_object=access_request
    )
    
    return access_request


@transaction.atomic
def review_access_request(
    access_request: RestrictedAccessRequest,
    reviewer: User,
    action: str,
    notes: str = ''
) -> RestrictedAccessRequest:
    """
    Admin review of access request
    
    SRS: Admin can approve, reject, or revoke access
    """
    if not reviewer.is_admin:
        raise PermissionDenied("Only admins can review access requests")
    
    if action == 'approve':
        access_request.approve(reviewer, notes)
        action_type = 'ACCESS_APPROVED'
        notification_type = 'ACCESS_APPROVED'
    
    elif action == 'reject':
        access_request.reject(reviewer, notes)
        action_type = 'ACCESS_REJECTED'
        notification_type = 'ACCESS_REJECTED'
    
    elif action == 'revoke':
        access_request.revoke(reviewer, notes)
        action_type = 'ACCESS_REVOKED'
        notification_type = 'ACCESS_REVOKED'
    
    else:
        raise ValidationError("Invalid action")
    
    # Create audit log
    create_audit_log(
        project=access_request.project,
        actor=reviewer,
        action_type=action_type,
        description=f"Access {action} for {access_request.investor.email}",
        metadata={'investor_email': access_request.investor.email}
    )
    
    # Create notification for investor
    from apps.notifications.services import create_notification
    create_notification(
        user=access_request.investor,
        notification_type=notification_type,
        title=f'Access Request {action.capitalize()}',
        message=f"Your access request for '{access_request.project.title}' has been {action}",
        related_object=access_request
    )
    
    return access_request


def check_restricted_access(user: User, project: Project) -> bool:
    """
    Check if user has access to restricted project data
    
    SRS: Backend enforcement is mandatory to prevent data leakage
    """
    if not user or not user.is_authenticated:
        return False
    
    # Admins and developers have full access
    if user.is_admin or user == project.developer:
        return True
    
    # Check if investor has approved access
    if user.is_investor:
        return RestrictedAccessRequest.objects.filter(
            investor=user,
            project=project,
            status=RestrictedAccessRequest.Status.APPROVED
        ).exists()
    
    return False


# ==================== AUDIT LOG SERVICES ====================

def create_audit_log(
    project: Project,
    actor: User,
    action_type: str,
    description: str = '',
    changes: Dict = None,
    metadata: Dict = None,
    request=None
) -> ProjectAuditLog:
    """
    Create audit log entry for project actions
    
    SRS: Audit trail for sensitive actions
    """
    log = ProjectAuditLog.objects.create(
        project=project,
        actor=actor,
        action_type=action_type,
        description=description,
        changes=changes or {},
        metadata=metadata or {},
        actor_ip=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
    )
    
    return log


# ==================== DASHBOARD SERVICES ====================

def get_developer_dashboard_data(user: User) -> Dict[str, Any]:
    """
    Get dashboard data for developers
    
    SRS: Developer dashboard with funding progress, investor count, etc.
    """
    projects = user.projects.all()
    
    total_projects = projects.count()
    approved_projects = projects.filter(status=Project.Status.APPROVED).count()
    pending_projects = projects.filter(status=Project.Status.PENDING_REVIEW).count()
    draft_projects = projects.filter(status=Project.Status.DRAFT).count()
    
    # Calculate funding metrics
    total_funding_secured = Decimal('0')
    total_investors = 0
    project_breakdown = []
    
    for project in projects.filter(status=Project.Status.APPROVED):
        # Get investment data
        investments = Investment.objects.filter(project=project)
        project_investors = investments.values('investor').distinct().count()
        
        project_data = {
            'id': str(project.id),
            'title': project.title,
            'status': project.status,
            'total_funding_secured': float(project.funding_secured),
            'funding_progress': project.funding_progress,
            'investor_count': project_investors,
            'shares_sold': project.shares_sold,
            'remaining_shares': project.remaining_shares,
            'days_remaining': project.days_remaining
        }
        project_breakdown.append(project_data)
        
        total_funding_secured += project.funding_secured
        total_investors += project_investors
    
    return {
        'summary': {
            'total_projects': total_projects,
            'approved_projects': approved_projects,
            'pending_projects': pending_projects,
            'draft_projects': draft_projects,
            'total_funding_secured': float(total_funding_secured),
            'total_investors': total_investors,
            'average_funding_rate': total_funding_secured / approved_projects if approved_projects else 0
        },
        'projects': project_breakdown,
        'updated_at': timezone.now()
    }


def get_investor_dashboard_data(user: User) -> Dict[str, Any]:
    """
    Get dashboard data for investors
    
    SRS: Investor dashboard with portfolio summary
    """
    investments = Investment.objects.filter(investor=user)
    
    total_investments = investments.count()
    active_investments = investments.filter(status='ACTIVE').count()
    completed_investments = investments.filter(status='COMPLETED').count()
    
    total_invested = sum(inv.amount for inv in investments)
    portfolio_value = sum(inv.current_value for inv in investments if hasattr(inv, 'current_value'))
    
    # Get investment breakdown by project
    investment_breakdown = []
    for investment in investments:
        project = investment.project
        investment_breakdown.append({
            'project_id': str(project.id),
            'project_title': project.title,
            'shares_owned': investment.shares,
            'investment_amount': float(investment.amount),
            'per_share_price': float(investment.per_share_price),
            'current_value': float(getattr(investment, 'current_value', investment.amount)),
            'status': investment.status,
            'invested_at': investment.created_at,
            'project_status': project.status
        })
    
    return {
        'summary': {
            'total_investments': total_investments,
            'active_investments': active_investments,
            'completed_investments': completed_investments,
            'total_invested': float(total_invested),
            'portfolio_value': float(portfolio_value),
            'estimated_return': float(portfolio_value - total_invested)
        },
        'investments': investment_breakdown,
        'updated_at': timezone.now()
    }