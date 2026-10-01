# Tutorial - jak spustit databazi (Supabase)

Projekt BuildMyPC nepouziva XAMPP, data jsou v Supabase (online).

Dashboard projektu:
https://supabase.com/dashboard/project/smjnwwkcokoofcmdtnhb

## Co potrebujes
- ucet na supabase.com
- Python 3
- internet

## Kde jsou klice
1. otevri projekt buildmypc
2. Settings (ozubene kolo) -> API
3. zkopiruj Project URL a anon key
4. jsou uz vyplnene v src/buildmypc.py

## Tabulka produkty
V Table Editoru je tabulka produkty:
- kod
- nazev
- skladem
- cena

Kdyz skladem klesne na 0, produkt zmizi z aplikace.

## Spusteni
```
pip install -r requirements.txt
python src/buildmypc.py
```

## Kdyz neco nefunguje
- nejde pripojeni -> zkontroluj internet a klice v kodu
- prazdny sklad -> mrkni do Table Editoru jestli tam jsou radky
- pouzivej anon key, ne service_role
