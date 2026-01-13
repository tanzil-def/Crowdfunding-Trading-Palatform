import django_filters
from apps.projects.models import Project
from apps.investments.models import Investment  # for InvestmentFilter

# --- Project Filter ---
class ProjectFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='category', lookup_expr='icontains')
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact')

    class Meta:
        model = Project
        fields = ['title', 'category', 'status']

# --- Investment Filter ---
class InvestmentFilter(django_filters.FilterSet):
    project_title = django_filters.CharFilter(field_name='project__title', lookup_expr='icontains')
    investor_email = django_filters.CharFilter(field_name='investor__email', lookup_expr='icontains')
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact')

    class Meta:
        model = Investment
        fields = ['project_title', 'investor_email', 'status']
