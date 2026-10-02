from django.contrib import admin
from .models import Category, Course, Cohort, Registration, ChatMessage, ContactInquiry


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class CohortInline(admin.TabularInline):
    model = Cohort
    extra = 1
    fields = ('cohort_code', 'start_date', 'end_date', 'max_seats', 'is_open_for_enrollment')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'category', 
        'duration_weeks', 
        'contact_hours', 
        'delivery_mode', 
        'fee', 
        'is_featured', 
        'is_active'
    )
    list_filter = ('category', 'delivery_mode', 'is_featured', 'is_active')
    search_fields = ('title', 'tagline', 'overview')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_featured', 'is_active')
    inlines = [CohortInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'tagline', 'overview')
        }),
        ('Curriculum & Delivery', {
            'fields': (
                'duration_weeks', 
                'contact_hours', 
                'delivery_mode', 
                'schedule_details', 
                'deliverables'
            )
        }),
        ('Commercials & Visibility', {
            'fields': ('fee', 'is_featured', 'is_active')
        }),
    )


@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = (
        'cohort_code', 
        'course', 
        'start_date', 
        'end_date', 
        'max_seats', 
        'enrolled_count', 
        'is_open_for_enrollment'
    )
    list_filter = ('is_open_for_enrollment', 'start_date', 'course__category')
    search_fields = ('cohort_code', 'course__title')
    list_editable = ('is_open_for_enrollment',)

    def enrolled_count(self, obj):
        return obj.registrations.count()
    enrolled_count.short_description = "Enrolled Candidates"


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 
        'email', 
        'phone', 
        'organization', 
        'cohort', 
        'experience_level', 
        'status', 
        'payment_status', 
        'created_at'
    )
    list_filter = ('status', 'payment_status', 'experience_level', 'cohort__course')
    search_fields = ('full_name', 'email', 'phone', 'organization', 'cohort__cohort_code')
    list_editable = ('status', 'payment_status')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Applicant Details', {
            'fields': ('full_name', 'email', 'phone', 'organization', 'experience_level')
        }),
        ('Enrollment Assignment', {
            'fields': ('cohort',)
        }),
        ('Status & Auditing', {
            'fields': ('status', 'payment_status', 'notes', 'created_at')
        }),
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_from_director', 'is_read', 'short_message', 'created_at')
    list_filter = ('is_from_director', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__email', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def short_message(self, obj):
        return obj.message[:60] + ('...' if len(obj.message) > 60 else '')
    short_message.short_description = "Message Snippet"


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('full_name', 'email', 'message')
    list_editable = ('is_resolved',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)