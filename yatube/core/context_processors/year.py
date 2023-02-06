import datetime


# Добавляет переменную с текущим годом.
def year(request):
    return {
        'year': int(datetime.datetime.now().strftime('%Y'))
    }
