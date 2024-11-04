"""Ferramentas para comunicação com o Excel"""

from typing import Any
from time import time
from pathlib import Path

import pandas as pd
from openpyxl.styles import Border, Side, Alignment

from accb.database import DatabaseManager
from accb.utils import get_time_hms, get_time_filename, log
from accb.model import Estab


def inject_into_db(db: DatabaseManager, city_name: str) -> Any:
    """Função para debug, injeta uma pesquisa com nome da cidade_todos.xlsx no banco de dados."""
    df = pd.read_excel("{}_todos.xlsx".format(city_name), skiprows=0, index_col=0)
    duration = get_time_hms(time())
    search_id = db.save_search(True, city_name, duration["minutes"])

    for _index, row in df.iterrows():
        (name, local, keyword, adress, price) = row

        info = {
            "search_id": search_id,
            "web_name": local,
            "adress": adress,
            "product_name": name,
            "price": price,
            "keyword": keyword,
        }
        db.save_search_item(info)

    return search_id


def db_to_xlsx(
    db: DatabaseManager,
    search_id: int,
    estabs: list[Estab],
    city: str,
    path: Path,
    filter_by_address: bool = True,
) -> Path:
    """Transforma uma dada pesquisa com id search_id em uma coleção de arquivos na pasta da cidade em questão (cidade) [data] [hora de geração dos arquivos]
    Retorna o caminho"""

    output_folder = path / f"{get_time_filename()} {city}"
    output_folder.mkdir(parents=True, exist_ok=True)

    for e in estabs:
        output_path = output_folder / f"{e.name}.xlsx"

        export_to_xlsx(
            db=db,
            search_id=search_id,
            filter_by_address=filter_by_address,
            output_path=output_path,
            web_name=e.web_name,
            adress=e.address,
        )

    return output_folder


def db_to_xlsx_all(city, search_id, db: DatabaseManager, path: Path) -> Path:
    query = """
    SELECT DISTINCT * FROM search_item
    WHERE search_item.web_name NOT IN (SELECT web_name FROM estab)
    AND search_id = ?
    GROUP BY web_name
    """

    result = db.run_query(query, (search_id,))

    output_folder = path / "Todos" / f"{get_time_filename()} {city}"
    output_folder.mkdir(parents=True, exist_ok=True)

    for _id, _product, web_name, adress, _price, _keyword in result:
        output_path = output_folder / f"{web_name}.xlsx"

        export_to_xlsx(
            db=db,
            search_id=search_id,
            filter_by_address=True,
            output_path=output_path,
            web_name=web_name,
            adress=adress,
        )

    return output_folder


def export_to_xlsx(
    db: DatabaseManager,
    search_id: int,
    filter_by_address: bool,
    output_path: Path,
    web_name: str,
    adress: str,
) -> None:
    log(f"Writing excel file to {output_path}...")

    products = db.run_query(
        "SELECT product_name, web_name, keyword, adress, price FROM search_item WHERE search_id=? AND web_name=? ORDER BY price ASC",
        (search_id, web_name),
    )

    df = pd.DataFrame(
        data=products,
        columns=[
            "PRODUTO",
            "ESTABELECIMENTO",
            "PALAVRA-CHAVE",
            "ENDEREÇO",
            "PREÇO",
        ],
    )

    if filter_by_address:
        pattern = "|".join(adress.upper().split(" "))
        df = df[df.ENDEREÇO.str.contains(pattern, regex=True)]

    # df = df[df.ENDEREÇO.str.contains(adress.upper())]
    writer = pd.ExcelWriter(str(output_path), engine="openpyxl")

    # TODO: use `with` statement

    df.to_excel(
        writer,
        sheet_name="Pesquisa",
        index=False,
        startrow=0,
        startcol=1,
        engine="openpyxl",
    )

    border = Border(
        left=Side(border_style="thin", color="FF000000"),
        right=Side(border_style="thin", color="FF000000"),
        top=Side(border_style="thin", color="FF000000"),
        bottom=Side(border_style="thin", color="FF000000"),
        diagonal=Side(border_style="thin", color="FF000000"),
        diagonal_direction=0,
        outline=True,
        vertical=Side(border_style="thin", color="FF000000"),
        horizontal=Side(border_style="thin", color="FF000000"),
    )

    workbook = writer.book["Pesquisa"]
    worksheet = workbook

    for w_name in "BCDEF":
        for cell in worksheet[w_name]:
            cell.border = border
            cell.alignment = Alignment(horizontal="center")

    for col in worksheet.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            max_length = max(max_length, len(str(cell.value)))
        adjusted_width = (max_length + 2) * 1.2
        worksheet.column_dimensions[column].width = adjusted_width

    writer.close()
