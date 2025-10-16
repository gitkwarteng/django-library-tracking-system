from datetime import timedelta

from django.db.models import Exists, OuterRef, Count, Q
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from library.models import Member, Loan


def get_loan_overdue_members():
    """
    Get all members with overdue loans
    """

    # Use subquery to check
    over_due_subquery = Loan.objects.filter(
        member_id=OuterRef('id'),
        due_date__lte=now().date(),
        is_returned=False
    )

    return Member.objects.filter(
        Exists(over_due_subquery)
    ).select_related(
        'user'
    ).only('id', 'user')


def get_member_overdue_book_title_values(member_id:int):
    """
    Get all overdue loans for a member

    Args:
        member_id (int): Member ID
    """
    return Loan.objects.filter(
        member_id=member_id,
        is_returned=False,
        due_date__lt=now().date(),
    ).select_related(
        'book'
    ).values(
        'book__title'
    )


def extend_loan_due_date_by(days:int, loan):
    """
    Extend a loan due date by the days specified.

    Args:
        days (int): Number of days to extend the due date
        loan (Loan): Loan object
    """

    # Check additional days isn't less than zero
    if days <= 0:
        raise ValidationError(detail='Additional days must be greater than zero')

    # Check loan isn't already returned
    if loan.is_returned:
        raise  ValidationError(detail='Loan already returned.')

    # Check loan isn't overdue
    if loan.is_overdue:
        raise  ValidationError('Loan already overdue.')

    loan.due_date = loan.due_date + timedelta(days=days)
    loan.save(update_fields=['due_date'])

    return loan


def get_top_active_members(number:int):
    """
    Get top active members with overdue loans
    Args:
        number (int): Number of members to return
    """

    return Member.objects.select_related(
        'user'
    ).annotate(
        active_loans=Count("loans", filter=Q(loans__is_returned=False))
    ).values(
        'id', 'user__username', 'user__email', 'active_loans'
    ).order_by('-active_loans')[:number]