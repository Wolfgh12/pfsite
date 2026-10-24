from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Category, 
    Course, 
    Cohort, 
    Registration, 
    ChatMessage, 
    ContactInquiry, 
    CourseModule,
    SiteSnippet,
    QuestionTicket,
    TicketMessage,
    ModuleQuestion
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(SiteSnippet)
class SiteSnippetAdmin(admin.ModelAdmin):
    list_display = ('key', 'page', 'label', 'status_badge', 'open_visual_editor')
    list_filter = ('page',)
    search_fields = ('key', 'label', 'value', 'default_value')
    readonly_fields = ('open_visual_editor',)

    fieldsets = (
        ('Location & Identity', {
            'fields': ('page', 'key', 'label', 'location_hint', 'open_visual_editor')
        }),
        ('Content Values', {
            'fields': ('value', 'default_value', 'is_multiline')
        }),
    )

    def status_badge(self, obj):
        if obj.value:
            return format_html('<span style="color:#F59E0B; font-weight:bold;">{}</span>', '● Custom Live')
        return format_html('<span style="color:#10B981; font-weight:bold;">{}</span>', '✓ Factory Default')
    status_badge.short_description = 'Status'

    def open_visual_editor(self, obj):
        url = f"{reverse('courses:director_site_editor')}?tab={obj.page}"
        return format_html(
            '<a class="button" style="background:#0F274C; color:#38BDF8; font-weight:bold; border:1px solid #38BDF8; border-radius:6px; padding:3px 8px; text-decoration:none;" href="{}" target="_blank">👁️ Studio &rarr;</a>',
            url
        )
    open_visual_editor.short_description = 'Live Studio'


class CohortInline(admin.TabularInline):
    model = Cohort
    extra = 1
    fields = ('cohort_code', 'start_date', 'end_date', 'max_seats', 'is_open_for_enrollment')


class CourseModuleInline(admin.TabularInline):
    model = CourseModule
    extra = 0
    fields = ('order', 'title', 'is_preview', 'slide_deck_url', 'open_module_studio')
    readonly_fields = ('open_module_studio',)
    ordering = ('order',)
    show_change_link = True

    def open_module_studio(self, obj):
        if not obj.id:
            return '-'
        url = f"{reverse('courses:director_site_editor')}?tab=modules&course_id={obj.course_id}&module_id={obj.id}"
        return format_html(
            '<a class="button" style="background:#051124; color:#34D399; font-weight:bold; border:1px solid #34D399; border-radius:6px; padding:2px 7px; text-decoration:none;" href="{}" target="_blank">🎓 Studio &rarr;</a>',
            url
        )
    open_module_studio.short_description = 'Classroom Studio'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'category', 
        'formatted_duration_display', 
        'contact_hours', 
        'delivery_mode', 
        'fee', 
        'is_featured', 
        'is_active',
        'open_visual_editor'
    )
    list_filter = ('category', 'delivery_mode', 'is_featured', 'is_active', 'level')
    search_fields = ('title', 'tagline', 'overview')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_featured', 'is_active')
    readonly_fields = ('open_visual_editor',)
    inlines = [CohortInline, CourseModuleInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'level', 'delivery_mode', 'open_visual_editor')
        }),
        ('Curriculum & Specifications', {
            'fields': (
                ('duration_weeks', 'duration_unit'), 
                'contact_hours', 
                'schedule_details', 
                'tagline',
                'overview',
                'deliverables'
            )
        }),
        ('Commercials & Visibility', {
            'fields': ('fee', 'is_featured', 'is_active')
        }),
    )

    def formatted_duration_display(self, obj):
        return obj.formatted_duration
    formatted_duration_display.short_description = 'Duration'

    def open_visual_editor(self, obj):
        if not obj.id:
            return '-'
        url = f"{reverse('courses:director_site_editor')}?tab=courses&course_id={obj.id}"
        return format_html(
            '<a class="button" style="background:#0A1C36; color:#F59E0B; font-weight:bold; border:1px solid #F59E0B; border-radius:6px; padding:3px 8px; text-decoration:none;" href="{}" target="_blank">⏱️ Edit Specs in Studio &rarr;</a>',
            url
        )
    open_visual_editor.short_description = 'Visual Editor'


class ModuleQuestionInline(admin.StackedInline):
    model = ModuleQuestion
    extra = 0
    fields = ('order', 'question_text', ('option_a', 'option_b'), ('option_c', 'option_d'), 'correct_option', 'explanation')
    ordering = ('order',)


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ('order', 'course', 'title', 'is_preview', 'open_visual_editor', 'open_assessment_desk', 'created_at')
    list_display_links = ('title',)
    list_filter = ('course', 'is_preview')
    search_fields = ('title', 'synopsis', 'lecture_notes')
    list_editable = ('order', 'is_preview')
    readonly_fields = ('open_visual_editor', 'open_assessment_desk', 'created_at')
    ordering = ('course', 'order')
    inlines = [ModuleQuestionInline]

    fieldsets = (
        ('Module Identification', {
            'fields': ('course', 'order', 'title', 'synopsis', 'is_preview', ('open_visual_editor', 'open_assessment_desk'))
        }),
        ('Presentation & Video Delivery', {
            'fields': ('slide_deck_url', 'slide_deck_file', 'video_url')
        }),
        ('Curriculum Outline & Notes', {
            'fields': ('lecture_notes',)
        }),
        ('System Audit', {
            'fields': ('created_at',)
        }),
    )

    def open_visual_editor(self, obj):
        if not obj.id:
            return '-'
        url = f"{reverse('courses:director_site_editor')}?tab=modules&course_id={obj.course_id}&module_id={obj.id}"
        return format_html(
            '<a class="button" style="background:#051124; color:#34D399; font-weight:bold; border:1px solid #34D399; border-radius:6px; padding:3px 8px; text-decoration:none;" href="{}" target="_blank">🎓 Studio &rarr;</a>',
            url
        )
    open_visual_editor.short_description = 'Classroom Studio'

    def open_assessment_desk(self, obj):
        if not obj.id:
            return '-'
        url = f"{reverse('courses:director_assessment_desk')}?course_id={obj.course_id}&module_id={obj.id}"
        return format_html(
            '<a class="button" style="background:#0F274C; color:#38BDF8; font-weight:bold; border:1px solid #38BDF8; border-radius:6px; padding:3px 8px; text-decoration:none;" href="{}" target="_blank">📝 Question Bank &rarr;</a>',
            url
        )
    open_assessment_desk.short_description = 'MCQ Bank'


@admin.register(ModuleQuestion)
class ModuleQuestionAdmin(admin.ModelAdmin):
    list_display = ('order', 'module', 'short_question', 'correct_option', 'created_at')
    list_filter = ('module__course', 'correct_option')
    search_fields = ('question_text', 'explanation', 'option_a', 'option_b', 'option_c', 'option_d')
    ordering = ('module', 'order')

    def short_question(self, obj):
        return obj.question_text[:70] + ('...' if len(obj.question_text) > 70 else '')
    short_question.short_description = 'Question Prompt'


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


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ('sender_type', 'sender_name', 'message', 'created_at')
    can_delete = False


@admin.register(QuestionTicket)
class QuestionTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'full_name', 'email', 'course', 'subject', 'status', 'created_at')
    list_filter = ('status', 'course', 'created_at')
    search_fields = ('ticket_number', 'full_name', 'email', 'subject', 'question')
    readonly_fields = ('ticket_number', 'created_at', 'answered_at')
    inlines = [TicketMessageInline]


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