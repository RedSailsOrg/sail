from django.conf import settings
from django.urls import include, path

import debug_toolbar


urlpatterns = [
    path('', include('articles.urls'))
]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
