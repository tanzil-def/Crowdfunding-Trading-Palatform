from decimal import Decimal
from django.db.models import Sum, F
from apps.projects.models import Project
from apps.investments.models import SharePurchase
from apps.favorites.models import Favorite
from apps.notifications.models import Notification
from apps.users.models import User


def get_unread_notifications_count(user):
    """
    Returns count of unread notifications for the given user.
    """
    return Notification.objects.filter(user=user, is_read=False).count()


def get_developer_dashboard(developer):
    """
    Developer dashboard metrics:
    - total projects
    - total shares sold
    - total investment received
    - pending projects
    - unread notifications
    """
    projects = Project.objects.filter(developer=developer)

    total_projects = projects.count()
    total_shares_sold = projects.aggregate(total=Sum('shares_sold'))['total'] or 0
    total_investment = projects.annotate(
        invested=F('shares_sold') * F('share_price')
    ).aggregate(total=Sum('invested'))['total'] or Decimal('0.00')
    pending_projects = projects.filter(status='PENDING').count()

    unread_notifications = get_unread_notifications_count(developer)

    return {
        "total_projects": total_projects,
        "total_shares_sold": total_shares_sold,
        "total_investment_received": total_investment,
        "pending_projects": pending_projects,
        "unread_notifications": unread_notifications
    }


def get_investor_dashboard(investor):
    """
    Investor dashboard metrics:
    - total investments
    - portfolio value
    - favorite projects
    - unread notifications
    """
    purchases = SharePurchase.objects.filter(investor=investor)
    total_investments = purchases.count()
    portfolio_value = purchases.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    favorite_projects = Favorite.objects.filter(investor=investor).count()
    unread_notifications = get_unread_notifications_count(investor)

    return {
        "total_investments": total_investments,
        "portfolio_value": portfolio_value,
        "favorite_projects": favorite_projects,
        "unread_notifications": unread_notifications
    }


def get_admin_dashboard():
    """
    Admin dashboard metrics:
    - total projects
    - pending projects
    - total investments
    - total revenue
    - unread notifications
    """
    total_projects = Project.objects.count()
    pending_projects = Project.objects.filter(status='PENDING').count()
    total_investments = SharePurchase.objects.count()
    total_revenue = SharePurchase.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # Fetch first admin user for notifications
    admin_user = User.objects.filter(role='ADMIN').first()
    unread_notifications = get_unread_notifications_count(admin_user) if admin_user else 0

    return {
        "total_projects": total_projects,
        "pending_projects": pending_projects,
        "total_investments": total_investments,
        "total_revenue": total_revenue,
        "unread_notifications": unread_notifications
    }
