from django.urls import path
from app.views import CreateWalletView, DepositView, TransferView, QueryStatementView
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('api/user/new/', CreateWalletView.as_view(), name='create_wallet'),
    path('api/wallet/deposit/', DepositView.as_view(), name='deposit'),
    path('api/wallet/transfer/', TransferView.as_view(), name='transfer'),
    path('web/wallet/statements/', views.query, name='query_statement'),
    path('web/wallet/statements/<int:account_id>/<int:count>', QueryStatementView.as_view(), name='results'),
]