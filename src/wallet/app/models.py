from django.db import models


class Account(models.Model):
    name = models.CharField(max_length=200, verbose_name="帳戶名稱")
    balance = models.DecimalField(default=0, max_digits=18, decimal_places=2, verbose_name="帳戶餘額")
    modified_time = models.DateTimeField(auto_now=True, verbose_name="帳戶更新時間")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="帳戶建立時間")

    def __str__(self):
        return f"id: {self.id}, name: {self.name}"

    class Meta:
        db_table = 'account_tab'


class Statement(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    wallet_id = models.IntegerField(default=0, verbose_name="帳戶編號")
    amount = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="交易金額")
    balance_after_transaction = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="交易後餘額")
    type = models.PositiveSmallIntegerField(verbose_name="帳戶編號")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="交易時間")

    def __str__(self):
        statement = f"transaction amount: {self.amount}, balance: {self.balance_after_transaction}, type: {self.type}, " \
                    f"transaction time: {self.create_time}"
        return statement

    class Meta:
        db_table = 'statement_tab'
