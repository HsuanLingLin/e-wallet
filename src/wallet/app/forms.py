from django import forms


class CreateWalletForm(forms.Form):
    name = forms.CharField(max_length=200, label="用戶名稱")


class DepositForm(forms.Form):
    wallet_id = forms.IntegerField(label="存款帳戶編號")
    amount = forms.DecimalField(max_digits=18, decimal_places=2, label="存入金額")

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('invalid amount')
        return amount


class TransferForm(forms.Form):
    from_wallet_id = forms.IntegerField(label="轉出帳號編號")
    to_wallet_id = forms.IntegerField(label="轉入帳號編號")
    amount = forms.DecimalField(max_digits=18, decimal_places=2, label="轉帳金額")

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('invalid amount')
        return amount
