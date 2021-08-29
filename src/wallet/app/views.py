import json
import logging

from enum import IntEnum
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from typing import NamedTuple
from app.models import Account
from app.forms import CreateWalletForm, DepositForm, TransferForm
from app.services import WalletService, CallBankApiService

logger = logging.getLogger('default')


def index(request):
    return HttpResponse("Hello world. You're at the e-wallet api index.")


class WalletResponse(NamedTuple):
    Result: int
    Message: str = None
    ResultObject: dict = None


class ResultCode(IntEnum):
    Success = 1
    Fail = 2
    InvalidRequestParameter = 9


# create new wallet
class CreateWalletView(View):
    form_class = CreateWalletForm

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self):
        result_object = {"error": 0}
        return JsonResponse(
            data=WalletResponse(
                Result=ResultCode.Success.value,
                ResultObject=result_object
            )._asdict())

    def post(self, request):
        """
        curl -X POST -H "Content-Type: application/json" -d '{"name":"Bob"}' "http://localhost:8080/api/user/new/"
        """
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception as e:
            logger.error(f'invalid body: %s\n%s', request.body, e)
            return JsonResponse(
                status=HttpResponseBadRequest.status_code,
                data=WalletResponse(
                    Result=ResultCode.InvalidRequestParameter.value,
                    Message='資料驗證錯誤'
                )._asdict()
            )

        form = self.form_class(body)
        if form.is_valid():
            name = form.cleaned_data['name']
            # create wallet service
            result_object = WalletService.create_wallet(name)
            return JsonResponse(
                data=WalletResponse(
                    Result=ResultCode.Success.value,
                    ResultObject=result_object
                )._asdict())
        else:
            return JsonResponse(
                status=HttpResponseBadRequest.status_code,
                data=WalletResponse(
                    Result=ResultCode.Fail.value,
                    Message="Invalid request parameters"
                )._asdict())


class DepositView(View):
    form_class = DepositForm

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self):
        result_object = {"error": 0}
        return JsonResponse(
            data=WalletResponse(
                Result=ResultCode.Success.value,
                ResultObject=result_object
            )._asdict())

    def post(self, request):
        """
        curl -X POST -H "Content-Type: application/json" -d '{"wallet_id":1, "amount":12.34}'
        "http://localhost:8080/api/wallet/deposit/"
        """
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception as e:
            logger.error(f'invalid body: %s\n%s', request.body, e)
            return JsonResponse(
                status=HttpResponseBadRequest.status_code,
                data=WalletResponse(
                    Result=ResultCode.InvalidRequestParameter.value,
                    Message='資料驗證錯誤'
                )._asdict()
            )

        form = self.form_class(body)
        if form.is_valid():
            wallet_id = form.cleaned_data['wallet_id']
            amount = form.cleaned_data['amount']
            try:
                # deposit service
                result_object = WalletService.deposit(wallet_id, amount)
                return JsonResponse(
                    data=WalletResponse(
                        Result=ResultCode.Success.value,
                        ResultObject=result_object
                    )._asdict())
            # DepositError include: Account.DoesNotExist, CallBankServiceError, InsufficientMoneyError
            except WalletService.DepositError as e:
                logger.error(f"Error: {e}")
                return JsonResponse(
                    data=WalletResponse(
                        Result=ResultCode.Fail.value,
                        Message="Deposit failed"
                    )._asdict())
        else:
            return JsonResponse(
                status=HttpResponseBadRequest.status_code,
                data=WalletResponse(
                    Result=ResultCode.Fail.value,
                    Message="Invalid request parameters"
                )._asdict())


class TransferView(View):
    form_class = TransferForm

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self):
        result_object = {"error": 0}
        return JsonResponse(
            data=WalletResponse(
                Result=ResultCode.Success.value,
                ResultObject=result_object
            )._asdict())

    def post(self, request):
        """
        curl -X POST -H "Content-Type: application/json" -d '{"from_wallet_id":2, "to_wallet_id": 1, "amount":10}'
        "http://localhost:8080/api/wallet/transfer/"
        """
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception as e:
            logger.error(f'invalid body: %s\n%s', request.body, e)
            return JsonResponse(
                status=HttpResponseBadRequest.status_code,
                data=WalletResponse(
                    Result=ResultCode.InvalidRequestParameter.value,
                    Message='資料驗證錯誤'
                )._asdict()
            )

        form = self.form_class(body)
        if form.is_valid():
            from_wallet_id = form.cleaned_data['from_wallet_id']
            to_wallet_id = form.cleaned_data['to_wallet_id']
            amount = form.cleaned_data['amount']
            try:
                # transfer service
                result_object = WalletService.transfer(from_wallet_id, to_wallet_id, amount)
                return JsonResponse(
                    data=WalletResponse(
                        Result=ResultCode.Success.value,
                        ResultObject=result_object
                    )._asdict())
            # TransferError include: WalletService.MoneyValueError, Account.DoesNotExist
            except WalletService.TransferError as e:
                logger.error(f"Error: {e}")
                return JsonResponse(
                    data=WalletResponse(
                        Result=ResultCode.Fail.value,
                        Message="Transfer failed"
                    )._asdict())
        else:
            return JsonResponse(
                status=HttpResponseBadRequest.status_code,
                data=WalletResponse(
                    Result=ResultCode.Fail.value,
                    Message="Invalid request parameters"
                )._asdict())


def query(request):
    account_list = Account.objects.all()
    context = {
        'account_list': account_list,
    }
    return render(request, 'app/query.html', context)


# allow use query the transactions from a certain wallet account by some filters
class QueryStatementView(View):
    http_method_names = ['get', 'post']

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, account_id, count=0):
        """
        get all transaction statements:
            http://localhost:8080/web/wallet/statements/1/0
        get recent numbers of transaction statements(e.g., 5):
            http://localhost:8080/web/wallet/statements/1/5
        """
        try:
            account = Account.objects.get(id=account_id)
            selected_wallet = account.statement_set.filter(wallet_id=account_id)
            if count != 0:
                statement_list = selected_wallet.order_by('-create_time')[:count]
            else:
                statement_list = selected_wallet.order_by('-create_time')
            return render(request, 'app/results.html', {'account': account, 'statement_list': statement_list})

        except Account.DoesNotExist:
            return JsonResponse(
                status=HttpResponseBadRequest.status_code,
                data=WalletResponse(
                    Result=ResultCode.Fail.value,
                    Message="The wallet does not exist"
                )._asdict())

    def post(self, account_id):
        """
        A web page to select wallet id:
            http://localhost:8080/web/wallet/statements/
        """
        try:
            account = Account.objects.get(id=account_id)
            return HttpResponseRedirect(reverse('results', args=(account.id,)))

        except Account.DoesNotExist:
            return JsonResponse(
                status=HttpResponseBadRequest.status_code,
                data=WalletResponse(
                    Result=ResultCode.Fail.value,
                    Message="The wallet does not exist"
                )._asdict())
