# ============================================================
# BuildMyPC - jednoducha OOP pokladna
# Python + tkinter (okno) + Supabase (databaze)
# ============================================================

# --- importy (knihovny ktere pouzivame) ---
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from supabase import create_client


# ============================================================
# TRIDA Databaze
# stara se o spojeni se Supabase a o tabulku "produkty"
# ============================================================
class Databaze:
    def __init__(self):
        # pripojeni k projektu na supabase (URL + anon klic)
        self.db = create_client(
            "https://smjnwwkcokoofcmdtnhb.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNtam53d2tjb2tvb2ZjbWR0bmhiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAyMzE1OTgsImV4cCI6MjEwNTgwNzU5OH0.AwuZdvdbLSSrEC6uAZSvH2c19BUYboMhaAUXLlj_4BM",
        )

    def nacti(self):
        # nacte produkty ktere jeste jsou skladem (skladem > 0)
        return self.db.table("produkty").select("*").gt("skladem", 0).order("kod").execute().data

    def odecist(self, kod, kusy):
        # po zaplaceni snizi pocet v databazi (zustane i po restartu!)
        odpoved = self.db.table("produkty").select("skladem").eq("kod", kod).single().execute()
        aktualni = odpoved.data["skladem"]
        nove = aktualni - kusy

        if nove <= 0:
            # uz nic neni -> smazat produkt uplne (pak se neobjevi po restartu)
            self.db.table("produkty").delete().eq("kod", kod).execute()
        else:
            # snizit sklad a ulozit do supabase
            self.db.table("produkty").update({"skladem": nove}).eq("kod", kod).execute()


# ============================================================
# TRIDA Uctenka
# jednoduche okno - doklad po zaplaceni (ID + polozky + celkem)
# ============================================================
class Uctenka(tk.Toplevel):
    def __init__(self, parent, polozky, celkem):
        super().__init__(parent)
        self.title("Účtenka")
        self.geometry("360x420")
        self.resizable(False, False)

        # --- tvorba ID uctenky ---
        # vezmeme aktualni datum a cas a slozime z toho unikatni kod
        # %Y = rok, %m = mesic, %d = den, %H = hodina, %M = minuta, %S = sekunda
        # priklad: U-20260324-102155
        self.id_uctenky = "U-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        cas = datetime.now().strftime("%d.%m.%Y %H:%M")  # datum na uctenku (pro cloveka)

        tk.Label(self, text="BuildMyPC - ÚČTENKA", font=("Segoe UI", 14, "bold")).pack(pady=8)
        tk.Label(self, text=f"ID: {self.id_uctenky}").pack()
        tk.Label(self, text=f"Datum: {cas}").pack()
        tk.Label(self, text="-" * 40).pack()

        # vypis polozek
        text = tk.Text(self, height=12, width=42, font=("Consolas", 10))
        text.pack(padx=10, pady=5)
        text.insert(tk.END, f"{'Kód':8} {'Ks':>4} {'Cena':>10}\n")
        text.insert(tk.END, "-" * 28 + "\n")
        for kod, p in polozky.items():
            castka = p["cena"] * p["mnozstvi"]
            text.insert(tk.END, f"{kod:8} {p['mnozstvi']:>4} {castka:>8} Kč\n")
        text.config(state="disabled")  # jen na cteni

        tk.Label(self, text="-" * 40).pack()
        tk.Label(self, text=f"CELKEM: {celkem} Kč", font=("Segoe UI", 12, "bold")).pack(pady=6)
        tk.Label(self, text="Děkujeme za nákup!").pack()

        tk.Button(self, text="Zavřít", bg="#1565c0", fg="white",
                  command=self.destroy).pack(pady=10)


# ============================================================
# TRIDA BuildMyPC
# hlavni okno aplikace (GUI) - zbozi vlevo, kosik vpravo
# ============================================================
class BuildMyPC(tk.Tk):
    def __init__(self):
        # --- nastaveni okna ---
        super().__init__()
        self.title("BuildMyPC")
        self.geometry("800x450")

        # --- promenne (data ktera drzime v pameti) ---
        self.db = Databaze()           # spojeni s databazi
        self.produkty = []             # seznam zbozi ze skladu
        self.kosik = {}                # co je v kosiku: kod -> {nazev, cena, mnozstvi}
        self.mnozstvi = tk.IntVar(value=1)  # kolik kusu chci pridat (+ / -)

        # ====================================================
        # LEVA CAST OKNA = dostupne zbozi
        # ====================================================
        leva = tk.LabelFrame(self, text="Zboží")
        leva.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.seznam = tk.Listbox(leva)  # vypis produktu
        self.seznam.pack(fill="both", expand=True)

        # tlacitka mnozstvi a pridani do kosiku
        tk.Button(leva, text="-", bg="#c62828", fg="white",
                  command=lambda: self.mnozstvi.set(max(1, self.mnozstvi.get() - 1))).pack(side="left")
        tk.Label(leva, textvariable=self.mnozstvi).pack(side="left")
        tk.Button(leva, text="+", bg="#2e7d32", fg="white",
                  command=lambda: self.mnozstvi.set(self.mnozstvi.get() + 1)).pack(side="left")
        tk.Button(leva, text="Do košíku", bg="#43a047", fg="white",
                  command=self.pridat).pack(fill="x")

        # ====================================================
        # PRAVA CAST OKNA = kosik + platba
        # ====================================================
        prava = tk.LabelFrame(self, text="Košík")
        prava.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.seznam_kosik = tk.Listbox(prava)  # vypis kosiku
        self.seznam_kosik.pack(fill="both", expand=True)

        # + / - meni mnozstvi u vybrane polozky v kosiku
        tk.Button(prava, text="-", bg="#c62828", fg="white",
                  command=lambda: self.zmen_kosik(-1)).pack(side="left")
        tk.Button(prava, text="+", bg="#2e7d32", fg="white",
                  command=lambda: self.zmen_kosik(1)).pack(side="left")
        self.lbl = tk.Label(prava, text="Celkem: 0 Kč")  # celkova cena
        self.lbl.pack()
        tk.Button(prava, text="ZAPLATIT", bg="#1565c0", fg="white",
                  command=self.zaplatit).pack(fill="x")

        # na zacatku nacteme zbozi z databaze
        self.obnov()

    # --------------------------------------------------------
    # obnov() = prekresli seznam zbozi i kosik
    # --------------------------------------------------------
    def obnov(self):
        # 1) nacti zbozi z supabase a vypis vlevo
        self.produkty = self.db.nacti()
        self.seznam.delete(0, tk.END)
        for p in self.produkty:
            self.seznam.insert(tk.END, f"{p['kod']} | {p['nazev']} | {p['skladem']} ks | {p['cena']} Kč")

        # 2) vypis kosik vpravo + spocitej celkem
        self.seznam_kosik.delete(0, tk.END)
        celkem = 0
        for kod, p in self.kosik.items():
            cena = p["cena"] * p["mnozstvi"]
            celkem += cena
            self.seznam_kosik.insert(tk.END, f"{kod} | {p['mnozstvi']} ks | {cena} Kč")
        self.lbl.config(text=f"Celkem: {celkem} Kč")

    # --------------------------------------------------------
    # pridat() = vybrany produkt da do kosiku
    # --------------------------------------------------------
    def pridat(self):
        i = self.seznam.curselection()  # ktery radek je oznaceny
        if not i:
            messagebox.showinfo("", "Vyber produkt.")
            return

        p = self.produkty[i[0]]
        kusy = self.mnozstvi.get()
        uz = self.kosik.get(p["kod"], {"mnozstvi": 0})["mnozstvi"]

        # kontrola jestli mame dost kusu na sklade
        if uz + kusy > p["skladem"]:
            messagebox.showwarning("", "Není skladem.")
            return

        # bud pridame kusy k existujici polozce, nebo vytvorime novou
        if p["kod"] in self.kosik:
            self.kosik[p["kod"]]["mnozstvi"] += kusy
        else:
            self.kosik[p["kod"]] = {"nazev": p["nazev"], "cena": p["cena"], "mnozstvi": kusy}

        self.mnozstvi.set(1)  # reset mnozstvi zpet na 1
        self.obnov()

    # --------------------------------------------------------
    # zmen_kosik() = +1 nebo -1 u vybrane polozky v kosiku
    # --------------------------------------------------------
    def zmen_kosik(self, zmena):
        i = self.seznam_kosik.curselection()
        if not i:
            return
        kod = list(self.kosik.keys())[i[0]]
        self.kosik[kod]["mnozstvi"] += zmena
        if self.kosik[kod]["mnozstvi"] <= 0:
            del self.kosik[kod]  # kdyz je 0, vyhodime z kosiku
        self.obnov()

    # --------------------------------------------------------
    # zaplatit() = odecte zbozi ze skladu a ukaze uctenku
    # --------------------------------------------------------
    def zaplatit(self):
        if not self.kosik:
            messagebox.showinfo("", "Košík je prázdný.")
            return

        # spocitat celkem jeste pred vyprazdnenim kosiku
        celkem = sum(p["cena"] * p["mnozstvi"] for p in self.kosik.values())
        kopie_kosiku = dict(self.kosik)  # kopie pro uctenku

        # ulozit odecteni do supabase (zustane i kdyz aplikaci vypnes)
        try:
            for kod, p in self.kosik.items():
                self.db.odecist(kod, p["mnozstvi"])
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodařilo se uložit do databáze:\n{e}")
            return

        self.kosik.clear()
        self.obnov()

        # otevre okno s dokladem (uctenkou)
        Uctenka(self, kopie_kosiku, celkem)


# ============================================================
# START PROGRAMU
# ============================================================
if __name__ == "__main__":
    BuildMyPC().mainloop()
