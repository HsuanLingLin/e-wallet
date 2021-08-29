import requests
import logging

from django.db import transaction
from django.db.models import F
from .models import Account
from enum import IntEnum
from django.utils import timezone

logger = logging.getLogger('default')


class TransactionType(IntEnum):
    Deposit = 1
    Transfer = 2


class CallBankApiService:
    class CallBankServiceError(Exception):
        """call bank api failed"""
    class BankAccountError(Exception):
        """error code is not zero"""

    @classmethod
    def call_bank_api(cls):
        try:
            response = requests.get("http://www.mocky.io/v2/5acadd1b2e00005600bbaa36?mocky-delay=3000ms")
            logger.info('Call bank API response msg: %s', response)
            response.raise_for_status()
            response_dic = response.json()
            error_code = response_dic['error']
            if error_code != 0:
                raise CallBankApiService.BankAccountError("[BankAccountError] Bank return value error")
        except (requests.exceptions.RequestException, CallBankApiService.BankAccountError) as e:
            logger.error("Error: <%s>", e)
            raise CallBankApiService.CallBankServiceError("[CallBankServiceError] Call bank service failed")


class WalletService:
    class InsufficientMoneyError(Exception):
        """餘額不足"""
    class MoneyValueError(Exception):
        """金額錯誤"""
    class DepositError(Exception):
        """存款操作失敗"""
    class TransferError(Exception):
        """轉帳操作失敗"""

    @classmethod
    def create_wallet(cls, name):
        account = Account(name=name)
        account.save()
        result_object = dict(error=0, wallet_id=account.id)
        return result_object

    @classmethod
    def deposit(cls, wallet_id, amount):
        try:
            with transaction.atomic():
                if amount <= 0:
                    raise WalletService.MoneyValueError("[MoneyInvalidError] Deposit money error.")

                # call bank api to make deduction
                CallBankApiService.call_bank_api()

                Account.objects.filter(id=wallet_id).update(balance=F('balance') + amount, modified_time=timezone.now())
                account = Account.objects.get(id=wallet_id)
                account.statement_set.create(wallet_id=wallet_id, amount=amount,
                                             balance_after_transaction=account.balance,
                                             type=TransactionType.Deposit)
                result_object = dict(error=0, new_balance=account.balance)
                return result_object

        except (Account.DoesNotExist, CallBankApiService.CallBankServiceError,
                WalletService.MoneyValueError) as e:
            logger.error("Error: <%s>", e)
            raise WalletService.DepositError(e)

    @classmethod
    def transfer(cls, from_wallet_id, to_wallet_id, amount):
        try:
            with transaction.atomic():
                if amount <= 0:
                    raise WalletService.MoneyValueError("[MoneyInvalidError] Transfer money error.")

                accounts = list(Account.objects.select_for_update().filter(id__in=[from_wallet_id, to_wallet_id]))
                # check wallet_id to identify from_wallet and to_wallet
                if accounts[0].id == from_wallet_id:
                    from_wallet, to_wallet = accounts[0], accounts[1]
                else:
                    from_wallet, to_wallet = accounts[1], accounts[0]

                from_wallet.balance -= amount
                if from_wallet.balance < 0:
                    raise WalletService.MoneyValueError("[MoneyInvalidError] Insufficient balance.")
                to_wallet.balance += amount
                from_wallet.save(update_fields=['balance', 'modified_time'])
                to_wallet.save(update_fields=['balance', 'modified_time'])

                from_wallet.statement_set.create(wallet_id=from_wallet_id, amount=-amount,
                                                 balance_after_transaction=from_wallet.balance,
                                                 type=TransactionType.Transfer)
                to_wallet.statement_set.create(wallet_id=to_wallet_id, amount=amount,
                                               balance_after_transaction=to_wallet.balance,
                                               type=TransactionType.Transfer)
                result_object = dict(error=0, new_balance=from_wallet.balance)
                return result_object
        except (WalletService.MoneyValueError, Account.DoesNotExist) as e:
            logger.error("Error: <%s>", e)
            raise WalletService.TransferError(e)
