from django.db import models


class Components(models.Model):
    comp_id = models.AutoField(primary_key=True)
    category = models.ForeignKey("Category", on_delete=models.PROTECT, null=True)
    comp_name = models.CharField(max_length=255)
    amount = models.IntegerField()

    # def __str__(self):
    #     return self.comp_name
    class Meta:
        verbose_name = "Component"
        verbose_name_plural = "Components"
        # ordering = ["id"]


class Devices(models.Model):
    device_id = models.BigAutoField(primary_key=True)
    device_name = models.CharField(max_length=255)

    # def __str__(self):
    #     return self.device_name
    class Meta:
        verbose_name = "Device"
        verbose_name_plural = "Devices"


class Category(models.Model):
    cat_id = models.AutoField(primary_key=True)
    cat_name = models.CharField(max_length=255)

    def __str__(self):
        return self.cat_name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        # ordering = ["id"]


class Connection(models.Model):
    device_id = models.IntegerField()
    comp_id = models.IntegerField()
    amount_need = models.IntegerField()


class OrderData(models.Model):
    comp_name = models.CharField(max_length=255)
    in_stock = models.IntegerField()
    amount_need = models.IntegerField()
    cat = models.IntegerField()
    enough = models.BooleanField(default=True)
    order_id = models.IntegerField(null=True)


class Replace(models.Model):
    comp_name = models.CharField(max_length=255)
    cat = models.IntegerField()
    in_stock = models.IntegerField(null=True)

    def __str__(self):
        return self.comp_name


class Orders(models.Model):
    device = models.ForeignKey("Devices", on_delete=models.PROTECT)
    amount_devices = models.IntegerField()


class ReplacedComponents(models.Model):
    order = models.ForeignKey("Orders", on_delete=models.PROTECT)
    old_comp = models.IntegerField()
    new_comp = models.ForeignKey("Components", on_delete=models.PROTECT, null=False)
