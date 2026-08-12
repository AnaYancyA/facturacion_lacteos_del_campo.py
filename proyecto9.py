import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

ARCHIVO="datos.json"

productos={
    "Queso Turrialba":3200,
    "Queso Molido":4300,
    "Natilla Pequeña":500,
    "Natilla Grande":1200,
    "Leche Agria":850
}

# ---------------- ARCHIVOS ----------------

def cargar_datos():

    if not os.path.exists(ARCHIVO):

        datos={
            "inventario":{p:20 for p in productos},
            "facturas":[]
        }

        with open(ARCHIVO,"w") as f:
            json.dump(datos,f)

    with open(ARCHIVO) as f:
        return json.load(f)

def guardar_datos(datos):

    with open(ARCHIVO,"w") as f:
        json.dump(datos,f,indent=4)

# ---------------- SISTEMA ----------------

class SistemaVentas:

    def __init__(self,root):

        self.root=root
        self.root.title("Sistema Lácteos del Campo")

        self.data=cargar_datos()
        self.carrito=[]

        tabs=ttk.Notebook(root)

        self.tab_ventas=ttk.Frame(tabs)
        self.tab_inventario=ttk.Frame(tabs)
        self.tab_facturas=ttk.Frame(tabs)
        self.tab_analisis=ttk.Frame(tabs)

        tabs.add(self.tab_ventas,text="Ventas")
        tabs.add(self.tab_inventario,text="Inventario")
        tabs.add(self.tab_facturas,text="Facturación")
        tabs.add(self.tab_analisis,text="Análisis")

        tabs.pack(expand=1,fill="both")

        self.crear_ventas()
        self.crear_inventario()
        self.crear_facturas()
        self.crear_analisis()

# ---------------- VENTAS ----------------

    def crear_ventas(self):

        tk.Label(self.tab_ventas,text="Cliente").pack()

        self.cliente=tk.Entry(self.tab_ventas)
        self.cliente.pack()

        tk.Label(self.tab_ventas,text="Producto").pack()

        self.combo_producto=ttk.Combobox(
            self.tab_ventas,
            values=list(productos.keys())
        )
        self.combo_producto.pack()

        tk.Label(self.tab_ventas,text="Cantidad").pack()

        self.cantidad=tk.Entry(self.tab_ventas)
        self.cantidad.pack()

        tk.Button(
            self.tab_ventas,
            text="Agregar al carrito",
            command=self.agregar_carrito
        ).pack()

        self.tree=ttk.Treeview(
            self.tab_ventas,
            columns=("producto","cantidad","precio")
        )

        self.tree.heading("#0",text="ID")
        self.tree.heading("producto",text="Producto")
        self.tree.heading("cantidad",text="Cantidad")
        self.tree.heading("precio",text="Precio")

        self.tree.pack(fill="both",expand=True)

        tk.Button(
            self.tab_ventas,
            text="Generar factura",
            command=self.generar_factura
        ).pack()

# ---------------- CARRITO ----------------

    def agregar_carrito(self):

        producto=self.combo_producto.get()

        try:
            cantidad=int(self.cantidad.get())
        except:
            messagebox.showwarning("Aviso","Cantidad inválida")
            return

        if cantidad>self.data["inventario"][producto]:

            messagebox.showwarning(
                "Stock",
                "No hay suficiente inventario"
            )
            return

        precio=productos[producto]

        self.carrito.append({
            "producto":producto,
            "cantidad":cantidad,
            "precio":precio
        })

        self.tree.insert(
            "",
            "end",
            text=len(self.carrito),
            values=(producto,cantidad,precio)
        )

# ---------------- FACTURA ----------------

    def generar_factura(self):

        subtotal = 0

        for item in self.carrito:

            subtotal += item["precio"] * item["cantidad"]
            self.data["inventario"][item["producto"]] -= item["cantidad"]

        iva = subtotal * 0.13
        total = subtotal + iva

        factura = {
            "cliente": self.cliente.get(),
            "fecha": str(datetime.now()),
            "items": self.carrito.copy(),
            "subtotal": subtotal,
            "iva": iva,
            "total": total
        }

        self.data["facturas"].append(factura)

        guardar_datos(self.data)

        # preguntar si desea guardar PDF
        guardar_pdf = messagebox.askyesno(
            "Guardar PDF",
            "¿Desea guardar la factura en PDF?"
        )

        if guardar_pdf:
            self.crear_pdf(factura)

        # -------- TIQUETE DE CAJA --------

        texto = ""
        texto += "\nLACTEOS DEL CAMPO\n"
        texto += "---------------------------------\n"
        texto += f"Cliente: {factura['cliente']}\n"
        texto += f"Fecha: {factura['fecha']}\n"
        texto += "---------------------------------\n"
        texto += "Producto        Cant   Precio   Subtotal\n"
        texto += "---------------------------------\n"

        for item in factura["items"]:

            producto = item["producto"]
            cantidad = item["cantidad"]
            precio = item["precio"]
            sub = cantidad * precio

            texto += f"{producto}   x{cantidad}   ₡{precio}   ₡{sub}\n"

        texto += "---------------------------------\n"
        texto += f"Subtotal: ₡{round(subtotal)}\n"
        texto += f"IVA 13%: ₡{round(iva)}\n"
        texto += f"TOTAL: ₡{round(total)}\n"
        texto += "---------------------------------\n"
        texto += "Gracias por su compra\n"

        messagebox.showinfo("Tiquete de Caja", texto)

        # limpiar carrito

        self.carrito = []
        self.tree.delete(*self.tree.get_children())

        self.cargar_historial()
        self.cargar_inventario()

# ---------------- PDF ----------------

    def crear_pdf(self,factura):

        archivo=filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")]
        )

        if not archivo:
            return

        c=canvas.Canvas(archivo,pagesize=letter)

        y=750

        c.drawString(100,y,"FACTURA - Lácteos del Campo")
        y-=30

        c.drawString(100,y,f"Cliente: {factura['cliente']}")
        y-=20

        c.drawString(100,y,f"Fecha: {factura['fecha']}")
        y-=40

        for i in factura["items"]:

            texto=f"{i['producto']} x{i['cantidad']} - ₡{i['precio']}"

            c.drawString(100,y,texto)

            y-=20

        y-=20

        c.drawString(100,y,f"Subtotal: ₡{factura['subtotal']}")
        y-=20
        c.drawString(100,y,f"IVA: ₡{factura['iva']}")
        y-=20
        c.drawString(100,y,f"TOTAL: ₡{factura['total']}")

        c.save()

        #messagebox.showinfo("PDF","Factura guardada")

# ---------------- INVENTARIO ----------------

    def crear_inventario(self):

        self.tree_inv=ttk.Treeview(
            self.tab_inventario,
            columns=("stock")
        )

        self.tree_inv.heading("#0",text="Producto")
        self.tree_inv.heading("stock",text="Stock")

        self.tree_inv.pack(fill="both",expand=True)

        frame=tk.Frame(self.tab_inventario)
        frame.pack(pady=10)

        tk.Label(frame,text="Producto").grid(row=0,column=0)

        self.prod_inv=ttk.Combobox(frame,values=list(productos.keys()))
        self.prod_inv.grid(row=0,column=1)

        tk.Label(frame,text="Cantidad").grid(row=0,column=2)

        self.cant_inv=tk.Entry(frame)
        self.cant_inv.grid(row=0,column=3)

        tk.Button(
            frame,
            text="Agregar Stock",
            command=self.agregar_stock
        ).grid(row=0,column=4,padx=10)

        tk.Button(
            frame,
            text="Exportar Excel",
            command=self.exportar_excel
        ).grid(row=0,column=5,padx=10)

        self.cargar_inventario()

    def cargar_inventario(self):

        self.tree_inv.delete(*self.tree_inv.get_children())

        for p,s in self.data["inventario"].items():

            if s<=5:
                texto=f"{s} ⚠ Bajo"
            else:
                texto=s

            self.tree_inv.insert("", "end", text=p, values=(texto))

# agregar stock

    def agregar_stock(self):

        producto=self.prod_inv.get()

        try:
            cantidad=int(self.cant_inv.get())
        except:
            messagebox.showwarning("Aviso","Cantidad inválida")
            return

        if producto=="":
            messagebox.showwarning("Aviso","Seleccione producto")
            return

        self.data["inventario"][producto]+=cantidad

        guardar_datos(self.data)

        messagebox.showinfo("Inventario","Stock actualizado")

        self.cargar_inventario()

# exportar excel

    def exportar_excel(self):

        datos=[]

        for p,s in self.data["inventario"].items():

            datos.append({
                "Producto":p,
                "Stock":s
            })

        df=pd.DataFrame(datos)

        archivo=filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel","*.xlsx")]
        )

        if archivo:

            df.to_excel(archivo,index=False)

            messagebox.showinfo("Excel","Inventario exportado")

# ---------------- FACTURAS ----------------

    def crear_facturas(self):

        self.tree_fact=ttk.Treeview(
            self.tab_facturas,
            columns=("cliente","fecha","total")
        )

        self.tree_fact.heading("#0",text="ID")
        self.tree_fact.heading("cliente",text="Cliente")
        self.tree_fact.heading("fecha",text="Fecha")
        self.tree_fact.heading("total",text="Total")

        self.tree_fact.pack(fill="both",expand=True)

        tk.Button(
            self.tab_facturas,
            text="Ver factura",
            command=self.ver_factura
        ).pack()

        tk.Button(
            self.tab_facturas,
            text="Editar factura",
            command=self.modificar_factura
        ).pack()

     
        tk.Button(
            self.tab_facturas,
            text="Eliminar factura",
            command=self.eliminar_factura
        ).pack()

        

        self.cargar_historial()

    def cargar_historial(self):

        self.tree_fact.delete(*self.tree_fact.get_children())

        for i,f in enumerate(self.data["facturas"]):

            self.tree_fact.insert(
                "",
                "end",
                text=i,
                values=(f["cliente"],f["fecha"],f["total"])
            )

    def ver_factura(self):

        sel = self.tree_fact.selection()

        if not sel:
            messagebox.showwarning("Aviso", "Seleccione una factura")
            return

        index = int(self.tree_fact.item(sel)["text"])
        factura = self.data["facturas"][index]

        subtotal = 0
        texto = ""

        texto += "\nLACTEOS DEL CAMPO\n"
        texto += "---------------------------------\n"
        texto += f"Cliente: {factura['cliente']}\n"
        texto += f"Fecha: {factura['fecha']}\n"
        texto += "---------------------------------\n"
        texto += "Producto        Cant   Precio   Subtotal\n"
        texto += "---------------------------------\n"

        for item in factura["items"]:

            producto = item["producto"]
            cantidad = item["cantidad"]
            precio = item["precio"]

            sub = cantidad * precio
            subtotal += sub

            texto += f"{producto}   x{cantidad}   ₡{precio}   ₡{sub}\n"

        iva = subtotal * 0.13
        total = subtotal + iva

        texto += "---------------------------------\n"
        texto += f"Subtotal: ₡{round(subtotal)}\n"
        texto += f"IVA 13%: ₡{round(iva)}\n"
        texto += f"TOTAL: ₡{round(total)}\n"
        texto += "---------------------------------\n"
        texto += "Gracias por su compra\n"

        messagebox.showinfo("Detalle de Factura", texto)




        # editar factura

    def modificar_factura(self):

        sel=self.tree_fact.selection()

        if not sel:
            return

        self.index=int(self.tree_fact.item(sel)["text"])

        factura=self.data["facturas"][self.index]

        self.ventana=tk.Toplevel(self.root)

        self.tree_edit=ttk.Treeview(
            self.ventana,
            columns=("producto","cantidad","precio")
        )

        self.tree_edit.heading("producto",text="Producto")
        self.tree_edit.heading("cantidad",text="Cantidad")
        self.tree_edit.heading("precio",text="Precio")

        self.tree_edit.pack()

        for i in factura["items"]:

            self.tree_edit.insert(
                "",
                "end",
                values=(i["producto"],i["cantidad"],i["precio"])
            )

        tk.Button(
            self.ventana,
            text="Editar producto",
            command=self.editar_producto
        ).pack()

        tk.Button(
            self.ventana,
            text="Guardar factura",
            command=self.guardar_factura_editada
        ).pack()

# editar producto

    def editar_producto(self):

        sel=self.tree_edit.selection()

        if not sel:
            return

        item=self.tree_edit.item(sel)

        prod,cant,precio=item["values"]

        v=tk.Toplevel(self.root)

        combo=ttk.Combobox(v,values=list(productos.keys()))
        combo.set(prod)
        combo.pack()

        entry=tk.Entry(v)
        entry.insert(0,cant)
        entry.pack()

        def guardar():

            nuevo=combo.get()
            cantidad=int(entry.get())
            precio=productos[nuevo]

            self.tree_edit.item(sel,values=(nuevo,cantidad,precio))

            v.destroy()

        tk.Button(v,text="Guardar",command=guardar).pack()

# guardar factura editada

    def guardar_factura_editada(self):

        items=[]
        subtotal=0

        for row in self.tree_edit.get_children():

            prod,cant,precio=self.tree_edit.item(row)["values"]

            cant=int(cant)
            precio=int(precio)

            subtotal+=cant*precio

            items.append({
                "producto":prod,
                "cantidad":cant,
                "precio":precio
            })

        iva=subtotal*0.13
        total=subtotal+iva

        self.data["facturas"][self.index]["items"]=items
        self.data["facturas"][self.index]["subtotal"]=subtotal
        self.data["facturas"][self.index]["iva"]=iva
        self.data["facturas"][self.index]["total"]=total

        guardar_datos(self.data)

        messagebox.showinfo("Guardado","Factura actualizada")

        self.ventana.destroy()

        self.cargar_historial()



    def eliminar_factura(self):

        sel=self.tree_fact.selection()

        if not sel:
            return

        index=int(self.tree_fact.item(sel)["text"])

        del self.data["facturas"][index]

        guardar_datos(self.data)

        self.cargar_historial()

# ---------------- ANALISIS ----------------

    def crear_analisis(self):

        tk.Button(
            self.tab_analisis,
            text="Gráfico ventas",
            command=self.grafico
        ).pack()

        tk.Button(
            self.tab_analisis,
            text="Proyección ventas",
            command=self.proyeccion
        ).pack()

    def grafico(self):

        datos=[]

        for f in self.data["facturas"]:
            for i in f["items"]:
                datos.append(i)

        df=pd.DataFrame(datos)

        ventas=df.groupby("producto")["cantidad"].sum()

        ventas.plot(kind="bar",color="red")

        plt.title("Ventas por producto")

        plt.show()

    def proyeccion(self):

        ventas=[f["total"] for f in self.data["facturas"]]

        if len(ventas)<2:
            messagebox.showwarning("Aviso","No hay suficientes datos")
            return

        X=np.array(range(len(ventas))).reshape(-1,1)
        y=np.array(ventas)

        modelo=LinearRegression()
        modelo.fit(X,y)

        futuro=np.array([[len(ventas)]])
        pred=modelo.predict(futuro)

        plt.plot(ventas,marker="o")
        plt.scatter(len(ventas),pred,color="red")

        plt.title("Proyección próxima venta")

        plt.show()

# ---------------- INICIO ----------------

root=tk.Tk()

app=SistemaVentas(root)

root.mainloop()
