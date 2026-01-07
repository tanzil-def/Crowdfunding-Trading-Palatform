from rest_framework.exceptions import ValidationError

def approve_access_request(access_request, admin_user):
    if access_request.status != 'PENDING':
        raise ValidationError("Only pending requests can be approved")
    access_request.status = 'APPROVED'
    access_request.decided_by = admin_user
    access_request.save(update_fields=['status', 'decided_by'])

def reject_access_request(access_request, admin_user, reason=None):
    if access_request.status != 'PENDING':
        raise ValidationError("Only pending requests can be rejected")
    access_request.status = 'REJECTED'
    access_request.reason = reason
    access_request.decided_by = admin_user
    access_request.save(update_fields=['status', 'reason', 'decided_by'])

def revoke_access_request(access_request, admin_user, reason=None):
    if access_request.status != 'APPROVED':
        raise ValidationError("Only approved requests can be revoked")
    access_request.status = 'REVOKED'
    access_request.reason = reason
    access_request.decided_by = admin_user
    access_request.save(update_fields=['status', 'reason', 'decided_by'])
