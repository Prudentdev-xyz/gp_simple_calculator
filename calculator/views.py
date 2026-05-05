from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Result, Course
from .utils import calculate_gp
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import io


@login_required(login_url='/auth/login/')
def calculate(request):
    if request.method == 'POST':
        num_courses = int(request.POST.get('num_courses', 0))
        courses     = []
        errors      = []

        for i in range(num_courses):
            code  = request.POST.get(f'course_code_{i}', '').strip()
            unit  = request.POST.get(f'credit_unit_{i}', '')
            score = request.POST.get(f'score_{i}', '')

            if not code or not unit or not score:
                errors.append(f'Row {i+1}: All fields are required.')
                continue

            try:
                unit  = int(unit)
                score = int(score)
            except ValueError:
                errors.append(f'Row {i+1}: Unit and Score must be numbers.')
                continue

            if not (1 <= unit <= 6):
                errors.append(f'Row {i+1}: Credit unit must be between 1 and 6.')
            if not (0 <= score <= 100):
                errors.append(f'Row {i+1}: Score must be between 0 and 100.')

            courses.append({
                'course_code': code,
                'credit_unit': unit,
                'score':       score,
            })

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'calculator/calculate.html', {
                'num_courses': num_courses,
                'num_range':   range(num_courses),
            })

        courses_copy = [c.copy() for c in courses]
        gp, total_units, total_gp, degree_class = calculate_gp(courses_copy)

        result = Result.objects.create(
            user               = request.user,
            total_units        = total_units,
            total_grade_points = total_gp,
            gp                 = gp,
            degree_class       = degree_class,
        )

        for c in courses_copy:
            Course.objects.create(
                result       = result,
                course_code  = c['course_code'],
                credit_unit  = c['credit_unit'],
                score        = c['score'],
                grade_point  = c['grade_point'],
                grade_letter = c['grade_letter'],
            )

        return redirect('result', pk=result.id)

    return render(request, 'calculator/calculate.html')


@login_required(login_url='/auth/login/')
def result(request, pk):
    result  = get_object_or_404(Result, id=pk, user=request.user)
    courses = result.courses.all()

    return render(request, 'calculator/result.html', {
        'result':  result,
        'courses': courses,
    })


@login_required(login_url='/auth/login/')
def download_pdf(request, pk):
    result  = get_object_or_404(Result, id=pk, user=request.user)
    courses = result.courses.all()

    html_string = render_to_string('calculator/result_pdf.html', {
        'result':  result,
        'courses': courses,
        'user':    request.user,
    })

    buffer = io.BytesIO()
    pisa.CreatePDF(html_string, dest=buffer)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="GP_Result.pdf"'
    return response