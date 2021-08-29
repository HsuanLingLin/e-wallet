from django.test import TestCase
from django.urls import reverse

from app.models import Account
from enum import IntEnum


class TransactionType(IntEnum):
    Deposit = 1
    Transfer = 2

def create_new_wallet(name):
    """
    Create a wallet with the given 'name'
    """
    new_wallet = Account.objects.create(name=name)
    return new_wallet


def deposit(wallet, amount):
    """
    Create a deposit statement
    """
    wallet.balance += amount
    wallet.save()
    wallet.statement_set.create(wallet_id=wallet.id, amount=amount,
                                balance_after_transaction=wallet.balance, type=TransactionType.Deposit)
    selected_wallet = wallet.statement_set.get(wallet_id=wallet.id)
    return selected_wallet


def transfer(from_wallet_id, to_wallet_id, amount):
    """
    Create transfer statements
    """
    from_account = Account.objects.get(id=from_wallet_id)
    to_account = Account.objects.get(id=to_wallet_id)
    from_account.balance -= amount
    to_account.balance += amount
    from_account.save()
    to_account.save()
    from_account.statement_set.create(wallet_id=from_wallet_id, amount=-amount,
                                      balance_after_transaction=from_account.balance, type=TransactionType.Transfer)
    to_account.statement_set.create(wallet_id=to_wallet_id, amount=amount,
                                    balance_after_transaction=to_account.balance, type=TransactionType.Transfer)
    transfer_account_statement = [from_account.statement_set.get(wallet_id=from_wallet_id,
                                                                 type=TransactionType.Transfer),
                                  to_account.statement_set.get(wallet_id=to_wallet_id, type=TransactionType.Transfer)]
    return transfer_account_statement


class CreateWalletViewTests(TestCase):
    def test_no_wallet(self):
        """
        If no account exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('query_statement'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No accounts are available.")
        self.assertQuerysetEqual(response.context['account_list'], [])

    def test_create_wallet(self):
        new_wallet = create_new_wallet(name="test")
        response = self.client.get(reverse('query_statement'))
        self.assertQuerysetEqual(
            response.context['account_list'],
            [f'<Account: id: {new_wallet.id}, name: {new_wallet.name}>']
        )

    def test_create_two_wallets(self):
        new_wallet = [create_new_wallet(name="test1"), create_new_wallet(name="test2")]
        response = self.client.get(reverse('query_statement'))
        self.assertQuerysetEqual(
            response.context['account_list'],
            [f'<Account: id: {new_wallet[0].id}, name: {new_wallet[0].name}>',
             f'<Account: id: {new_wallet[1].id}, name: {new_wallet[1].name}>'], ordered=False
        )


class QueryStatementViewTests(TestCase):
    def test_no_statement(self):
        """
        If no transaction statement exist, an appropriate message is displayed.
        """
        new_wallet = create_new_wallet(name="test")
        count = 0
        url = reverse('results', args=(new_wallet.id, count))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No transaction statements are available.")
        self.assertQuerysetEqual(response.context['statement_list'], [])

    def test_deposit_statement(self):
        """
        <Statement: transaction amount: 1000.00000, balance: 1000.00000, type: 1, transaction time:
        2020-07-10 11:58:06.009182+00:00>
        """
        wallet = create_new_wallet(name="test")
        amount, count = 1000, 0
        selected_wallet = deposit(wallet, amount)
        url = reverse('results', args=(wallet.id, count))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(wallet.balance, selected_wallet.balance_after_transaction)
        self.assertQuerysetEqual(
            response.context['statement_list'],
            [f'<Statement: transaction amount: {selected_wallet.amount}, '
             f'balance: {selected_wallet.balance_after_transaction}, type: {selected_wallet.type}, '
             f'transaction time: {selected_wallet.create_time}>'])

    def test_transfer_statement(self):
        new_wallet = [create_new_wallet(name="test1"), create_new_wallet(name="test2")]
        amount, count = 1000, 0
        selected_wallet = deposit(new_wallet[0], amount)
        transfer_account = transfer(new_wallet[0].id, new_wallet[1].id, amount)
        # 1. test from wallet id statement (include transfer statement and deposit statement)
        url = reverse('results', args=(transfer_account[0].wallet_id, count))
        response = self.client.get(url)
        self.assertQuerysetEqual(
            response.context['statement_list'],
            [f'<Statement: transaction amount: {transfer_account[0].amount}, '
             f'balance: {transfer_account[0].balance_after_transaction}, type: {transfer_account[0].type}, '
             f'transaction time: {transfer_account[0].create_time}>',
             f'<Statement: transaction amount: {selected_wallet.amount}, '
             f'balance: {selected_wallet.balance_after_transaction}, type: {selected_wallet.type}, '
             f'transaction time: {selected_wallet.create_time}>'])
        # 2. test to wallet id statement (only transfer statement)
        url = reverse('results', args=(transfer_account[1].wallet_id, count))
        response = self.client.get(url)
        self.assertQuerysetEqual(
            response.context['statement_list'],
            [f'<Statement: transaction amount: {transfer_account[1].amount}, '
             f'balance: {transfer_account[1].balance_after_transaction}, type: {transfer_account[1].type}, '
             f'transaction time: {transfer_account[1].create_time}>'])
