from django.shortcuts import redirect
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import *
from .utils import *
from django.db.models import QuerySet

import sqlite3
from django.views.decorators.cache import cache_page
from django.core.cache import cache


# class MoveDataAPI(APIView):
#     def get(self, request):
#         with sqlite3.connect("db.sqlite3") as connection:
#             cur = connection.cursor()
#             data = cur.execute("SELECT * FROM сomponents_components ORDER BY id").fetchall()
#             print(data)
#             # for d in data:
#             #     Devices.objects.create(comp_name=d[1], price=d[2], description=d[3], photo=d[4], is_published=d[5],
#             #                             category_id=d[6], country_id=d[7])
#             return Response({"ok":"ok"})


class CompAPIView(generics.ListAPIView):
    queryset = Components.objects.all()
    serializer_class = IndexSerializer
    # def get(self, request):
        # comp_list = cache.get("comp_list")
        # if comp_list:
        #     return Response(comp_list)
        # data = Components.objects.all().values("comp_id", "comp_name", "amount", "category")
        # components = Components.objects.all().select_related('category')
        # serializer = IndexSerializer(components, many=True)
        # return Response(serializer.data)
        # print(data)
        # cache.set("comp_list", data, 60)
        # return Response(data)
    # permission_classes = (IsAuthenticated, )


class ConsAPIView(APIView):
    permission_classes = (IsAuthenticated, )
    def get(self, request):
        consumables = Consumables.objects.all().values()
        return Response(consumables)


# class SortedComps(APIView):
#     def get(self, request):
#         components = Components.objects.all().values()
#         sorted_comps = []
#         category_ids = [1, 5, 3, 6, 2, 4, 9, 7, 8, 10]
#
#         for cat_id in category_ids:
#             for component in components:
#                 if component["category_id"] == cat_id:
#                     sorted_comps.append(component)
#
#         # print(sorted_components)
#         return Response(sorted_comps)


class DeviceAPI(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        values = Devices.objects.values_list("device_name", flat=True)
        return Response({"device_names": values})

    def post(self, request):
        comp_ids = []
        amount_need = []
        serializer = CompSerializer(data=request.data)
        serializer.is_valid()
        name = request.data["device_name"]
        device_need = request.data["device_need"]
        print(request.data)
        device_id = Devices.objects.get(device_name=name).device_id
        connection_data = Connection.objects.filter(device_id=device_id).values()

        order = Orders.objects.create(device_id=device_id, amount_devices=device_need)
        order.save()

        for con in connection_data:
            comp_ids.append(con["comp_id"])
            amount_need.append(con["amount_need"])

        amount_need_all = [i * int(device_need) for i in amount_need]

        comps_data = Components.objects.filter(comp_id__in=comp_ids).values_list("comp_name", "amount", "category")

        data = OrderData.objects.all()
        data.delete()
        print(amount_need_all)
        for i in range(len(amount_need_all)):
            data_instance = OrderData.objects.create(comp_name=comps_data[i][0], in_stock=comps_data[i][1], amount_need=amount_need_all[i], cat=comps_data[i][2], enough=1, order_id=order.id)
            data_instance.save()

        return redirect("show")


class ShowOrderAPI(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        info = OrderData.objects.all().values("id", "comp_name", "in_stock", "amount_need", "cat")
        sorted_info = []

        category_ids = [1, 5, 3, 6, 2, 4, 9, 7, 8, 10]
        i = 0
        for cat_id in category_ids:
            for component in info:
                if component["cat"] == cat_id:
                    component["id"] = i
                    i += 1
                    sorted_info.append(component)

        comp_name = []
        in_stock = []
        amount_need = []
        cat = []
        order_data = OrderData.objects.all().values()
        for component in order_data:
            comp_name.append(component["comp_name"])
            in_stock.append(component["in_stock"])
            amount_need.append(component["amount_need"])
            cat.append(component["cat"])
        print(sorted_info)

        for i in range(len(in_stock)):
            if in_stock[i] < amount_need[i]:
                comp_name_ = comp_name[i]
                cat_rep = cat[i]
                Replace.objects.all().delete()
                OrderData.objects.filter(comp_name=comp_name_).update(enough=0)
                comp_for_rep = Components.objects.filter(
                    Q(amount__gte=amount_need[i]) & Q(category_id=cat_rep)).values("comp_name", "amount")
                for c in comp_for_rep:
                    Replace.objects.create(comp_name=c["comp_name"], in_stock=c["amount"], cat=cat_rep)
                return redirect("replace")

        for i in range(len(comp_name)):
            amount = Components.objects.filter(comp_name=comp_name[i]).values("amount")[0]["amount"]
            print(amount)
            amount -= amount_need[i]
            OrderData.objects.filter(comp_name=comp_name[i]).update(in_stock=amount)
            Components.objects.filter(comp_name=comp_name[i]).update(amount=amount)

        # return Response({"status": 200, "order_data": ShowSerializer(info, many=True).data})
        return Response({"status": 200, "order_data": sorted_info})


class ReplaceAPI(APIView):
    permission_classes = (IsAuthenticated, )
    def get(self, request):
        # comps_to_replace = Replace.objects.all().values_list("comp_name", flat=True)
        comp_name = OrderData.objects.filter(enough=0).values("comp_name")[0]["comp_name"]
        comps_to_replace = Replace.objects.values("id", "comp_name", "in_stock")

        return Response({"status": 400, "comp_to_replace": comp_name, "comp_data": comps_to_replace})

    def post(self, request):
        serializer = ReplaceSerializer(data=request.data)
        if serializer.is_valid():
            comp_name = request.data["replacement_choice"]
            new_comp_id = Components.objects.filter(comp_name=comp_name).values("comp_id")[0]["comp_id"]
            old_comp = OrderData.objects.filter(enough=0).values("comp_name")[0]["comp_name"]
            old_comp_id = Components.objects.filter(comp_name=old_comp).values("comp_id")[0]["comp_id"]
            print(old_comp_id)
            order_id = OrderData.objects.get(comp_name=old_comp).order_id
            ReplacedComponents.objects.create(new_comp_id=new_comp_id, old_comp=old_comp_id, order_id=order_id)

            in_stock = Components.objects.filter(comp_name=comp_name).values("amount")
            OrderData.objects.filter(enough=0).update(enough=1, comp_name=str(comp_name), in_stock=in_stock)
            return redirect("show")
        return Response({"status": 400, "response": "Data is not valid"})


class UpdateComponentAPI(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        serializer = UpdateComponentSerializer(data=request.data)
        if serializer.is_valid():
            component = Components.objects.get(comp_name=request.data["comp_name"])
            new_amount = component.amount + request.data["amount_add"]
            Components.objects.filter(comp_name=request.data["comp_name"]).update(amount=new_amount)

            # print(component)
            return Response({"status": 200})
        return Response({"status": 400, "response": "Data is not valid"})


class UpdateDBAPI(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        values = Components.objects.values_list("comp_name", flat=True)
        categories = Category.objects.values_list("cat_name", flat=True)
        return Response({"status": 200, "comp_names": values, "categories": categories})

    def post(self, request):
        for comp in request.data:
            serializer = UpdateSerializer(data=comp)
            # if serializer.is_valid():
            if serializer.is_valid():
                amount_add = int(comp["amount_add"])
                try:
                    comp_name = comp["comp_name"]
                    component = Components.objects.get(comp_name=comp_name)
                    new_amount = component.amount + amount_add
                    Components.objects.filter(comp_name=comp_name).update(amount=new_amount)

                except:
                    component = Category.objects.get(cat_name=comp["category"])
                    category = component
                    Components.objects.create(comp_name=comp["comp_name"], category=category, amount=comp["amount_add"])
                    print("Success new ")

            else:
            # return redirect("home")
                return Response({"status": 400, "response": "Invalid request data"})
        return Response({"status": 200, "response": "Data was successfully added!"})


class AddNewDeviceAPI(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        components = Components.objects.values("comp_id", "comp_name")
        # consumables = Consumables.objects.values()
        # comps_list = list(components)
        # cons_list = list(consumables)
        # for cons in cons_list:
        #     cons["comp_id"] += components.reverse().first()["comp_id"]
        # print(consumables)
        #
        # comps = comps_list + cons_list
        # print(components.reverse().first())
        return Response({"status": 200, "data": components})

    def post(self, request):
        serializer = AddNewDeviceSerializer(data=request.data)
        if serializer.is_valid():
            device_name = request.data["device_name"]
            comp_data = request.data["comp_data"]
            # try:
            device = Devices.objects.filter(device_name=device_name)
            if device:
                # print(device)
                return Response({"status": 400, "response": "Device already exists"})
            # except :
            else:
                Devices.objects.create(device_name=device_name)
                device_id = Devices.objects.get(device_name=device_name).device_id
                for component in comp_data:
                    comp_name = component["comp_name"]
                    amount_need = component["amount_need"]
                    comp_id = Components.objects.get(comp_name=comp_name).comp_id
                    Connection.objects.create(device_id=device_id, comp_id=comp_id, amount_need=amount_need)
            # Devices.objects.create(device_name=device_name)
            # device_id = Devices.objects.get(device_name=device_name).id
            # for component in comp_data:
            #     comp_name = component["comp_name"]
            #     amount_need = component["amount_need"]
            #     comp_id = Components.objects.get(comp_name=comp_name).comp_id
            #     Connection.objects.create(device_id=device_id, comp_id=comp_id, amount_need=amount_need)

            return Response({"status": 200, "response": "Device has been successfully added to database! "})
        return Response({"status": 400, "response": "Invalid request data"})

    def put(self, request):
        serializer = UpdateDeviceSerializer(data=request.data)
        if serializer.is_valid():
            components = Connection.objects.filter(device_id=request.data["device_id"]).delete()
            for component in request.data["comp_data"]:
                data = Connection.objects.create(device_id=request.data["device_id"], comp_id=component["comp_id"], amount_need=component["amount_need"])
                data.save()
            return Response({"status": "200"})
        return Response({"status": "400", "response": "Data is not valid"})






# class MoveDataAPI(APIView):
#     def get(self, request):
#         with sqlite3.connect("db.sqlite3") as connection:
#             cur = connection.cursor()
#             # data = cur.execute("SELECT * FROM components_components ORDER BY comp_id").fetchall()
#             # print(data)
#             # for d in data:
#             #     cat = Category.objects.get(cat_id=d[3])
#             #     Components.objects.create(comp_name=d[1], amount=d[2], category=cat)
#             data = cur.execute("SELECT * FROM components_connection ORDER BY id").fetchall()
#             print(data)
#             for d in data:
#
#                 Connection.objects.create(device_id=d[1], comp_id=d[2], amount_need=d[3])
#             return Response({"ok": "ok"})


class OrdersAPIView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        orders = Orders.objects.all().values()

        orders_id = [{"order_id": order["id"]} for order in orders]
        devices_id = [order["device_id"] for order in orders]
        amount_devices = [{"amount_devices": order["amount_devices"]} for order in orders]
        creation_date = [{"creation_date": order["date"]} for order in orders]

        components_id = []
        amount_components = []
        devices_name = []

        for i in range(len(devices_id)):
            devices_name.append(Devices.objects.filter(device_id=devices_id[i]).values("device_name")[0])

            components = Connection.objects.filter(device_id=devices_id[i]).values("comp_id")
            components_id.append([component["comp_id"] for component in components])

            components_need = Connection.objects.filter(device_id=devices_id[i]).values('amount_need')
            amount_components.append([{"amount_need": component_need["amount_need"] * amount_devices[i]["amount_devices"]} for component_need in components_need])

        for i in range(len(orders_id)):
            replaced_components = (ReplacedComponents.objects.
                                        filter(order_id=orders_id[i]["order_id"]).
                                        values("old_comp", "new_comp_id"))

            if replaced_components:
                for replaced_component in replaced_components:
                    old_component = replaced_component["old_comp"]
                    new_component = replaced_component["new_comp_id"]

                    components_id[i][components_id[i].index(old_component)] = new_component

        component_names = []
        for component_id in components_id:
            component_names.append(Components.objects.filter(comp_id__in=component_id).values("comp_name"))

        component_data = []
        components_data = []
        for i in range(len(component_names)):
            for j in range(len(component_names[i])):
                component_data.append(component_names[i][j] | amount_components[i][j])
            components_data.append({"comp_data": component_data})
            component_data = []

        orders_data = []
        for i in range(len(orders_id)):
            creation_date[i]["creation_date"] = str(creation_date[i]["creation_date"])[:10] + " " + str(creation_date[i]["creation_date"])[11:16]
            order_data = orders_id[i] | devices_name[i] | amount_devices[i] | creation_date[i] | components_data[i]
            orders_data.append(order_data)
            order_data = []

        return Response(orders_data)


class DeviceSpecsAPiView(APIView):
    def get(self, request):
        devices = Devices.objects.all().values()
        components_id = []
        components_need = []
        components_data_id = []

        for device in devices:
            components = Connection.objects.filter(device_id=device["device_id"]).values("comp_id")

            components_id.append([component["comp_id"] for component in components])

            components_need_1 = Connection.objects.filter(device_id=device["device_id"]).values('amount_need')
            components_need.append(components_need_1)
        component_names = []
        for component_id in components_id:
            components_data_id.append([{"comp_id": comp_id} for comp_id in component_id])
            component_names.append(Components.objects.filter(comp_id__in=component_id).values("comp_name"))

        component_data = []
        components_data = []

        for i in range(len(component_names)):
            for j in range(len(component_names[i])):
                component_data.append(components_data_id[i][j] | component_names[i][j] | components_need[i][j])
            components_data.append({"comp_data": component_data})
            component_data = []
        data = []
        for i in range(len(devices)):
            data.append(devices[i] | components_data[i])

        return Response(data)


