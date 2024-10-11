import pandas as pd
import numpy as np
import database
import jellyfish
from openpyxl.styles import Border, Side, Alignment


class Keyword:
    def __init__(self, name, product_name, rate=0, similarity=0):

        self.name = name
        self.product_name = product_name
        self.rate = rate
        self.similarity = similarity


class KeywordTrainer:

    db = database.Database()
    products = db.db_get_product()
    products = [
        {"name": product[0], "keywords": product[1].split(",")} for product in products
    ]

    def __init__(self):

        self.dataset = pd.read_excel("dataset.xlsx", index_col=0)
        self.dataset_unique = self.dataset.drop_duplicates(
            subset=["PRODUTO", "KEYWORD"], keep="first"
        )
        self.keyword_rate = self.dataset.groupby("KEYWORD").count()
        self.keyword_rate = dict(self.keyword_rate.to_records())
        self.product_rate = self.dataset.groupby("PRODUTO").count()
        self.product_rate = dict(self.product_rate.to_records())

        self.keyword_log = []

    def evaluate_keyword(self):

        self.keyword_string = []

        with open("keyword.log", "w+") as outfile:

            for index, row in self.dataset_unique.iterrows():

                try:
                    product, keyword = row
                    similarity = jellyfish.jaro_distance(product, keyword)
                    # similarity = jellyfish.levenshtein_distance(product, keyword)
                    # similarity = jellyfish.damerau_levenshtein_distance(product, keyword)

                    # import jellyfish
                    # jellyfish.levenshtein_distance(u'jellyfish', u'smellyfish')
                    # 2
                    # jellyfish.jaro_distance(u'jellyfish', u'smellyfish')
                    # 0.89629629629629637
                    # jellyfish.damerau_levenshtein_distance(u'jellyfish', u'jellyfihs')
                    # 1

                    rate = self.product_rate[product]
                    k_rate = self.keyword_rate[keyword]

                    new_string = product.replace(keyword, "")
                    for key in keyword.split():
                        new_string = new_string.replace(key, "")
                    new_string = new_string.replace("1 KG", "")
                    new_string = new_string.replace("1KG", "")
                    new_string = new_string.replace("1K", "")
                    new_string = new_string.replace("1 K", "")
                    new_string = new_string.replace("250GR", "")
                    new_string = new_string.replace("250G", "")
                    new_string = new_string.replace("500G", "")
                    new_string = new_string.replace("900ML", "")
                    new_string = new_string.replace("KG", "")
                    new_string = new_string.replace("GR", "")

                    outfile.write("{} = {}\n".format(product, new_string))
                    self.keyword_log.append(
                        [product, keyword, new_string, similarity, rate, k_rate]
                    )
                    if new_string.replace(" ", "") != "":
                        self.keyword_string.append([product, keyword, new_string])
                except:
                    print("String mal formatada.")
                    pass

        self.evaluate_to_xlsx()
        # self.keyword_string_to_xlsx()

    def keyword_string_to_xlsx(self):

        df = pd.DataFrame(
            data=self.keyword_string,
            columns=[
                "PRODUTO",
                "KEYWORD",
                "NEWSTRING",
            ],
        )

        writer = pd.ExcelWriter("keyword_string.xlsx", engine="openpyxl")

        df = df.sort_values(by=["PRODUTO", "KEYWORD"])

        df = df.to_excel(
            writer, sheet_name="Keyword", index=False, startrow=0, startcol=1
        )
        border = Border(
            left=Side(border_style="thin", color="FF000000"),
            right=Side(border_style="thin", color="FF000000"),
            top=Side(border_style="thin", color="FF000000"),
            bottom=Side(border_style="thin", color="FF000000"),
            diagonal=Side(border_style="thin", color="FF000000"),
            diagonal_direction=0,
            outline=Side(border_style="thin", color="FF000000"),
            vertical=Side(border_style="thin", color="FF000000"),
            horizontal=Side(border_style="thin", color="FF000000"),
        )

        workbook = writer.book["Keyword"]
        worksheet = workbook
        for cell in worksheet["B"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for cell in worksheet["C"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for cell in worksheet["D"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            worksheet.column_dimensions[column].width = adjusted_width

        writer.save()

    def evaluate_to_xlsx(self):

        df = pd.DataFrame(
            data=self.keyword_log,
            columns=[
                "PRODUTO",
                "KEYWORD",
                "SPURIOUS",
                "SIMILARITY",
                "P_RATE",
                "K_RATE",
            ],
        )

        # REMOVER ESPAÇOS DA STRING E DEPOIS DA UM MERGE-DUPLICATES

        writer = pd.ExcelWriter("keyword_log.xlsx", engine="openpyxl")

        df = df.sort_values(by=["KEYWORD", "SIMILARITY"])

        df = df.to_excel(
            writer, sheet_name="Dataset", index=False, startrow=0, startcol=1
        )
        border = Border(
            left=Side(border_style="thin", color="FF000000"),
            right=Side(border_style="thin", color="FF000000"),
            top=Side(border_style="thin", color="FF000000"),
            bottom=Side(border_style="thin", color="FF000000"),
            diagonal=Side(border_style="thin", color="FF000000"),
            diagonal_direction=0,
            outline=Side(border_style="thin", color="FF000000"),
            vertical=Side(border_style="thin", color="FF000000"),
            horizontal=Side(border_style="thin", color="FF000000"),
        )

        workbook = writer.book["Dataset"]
        worksheet = workbook
        for cell in worksheet["B"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for cell in worksheet["C"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for cell in worksheet["D"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for cell in worksheet["E"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for cell in worksheet["F"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for cell in worksheet["G"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            worksheet.column_dimensions[column].width = adjusted_width

        writer.save()


if __name__ == "__main__":

    trainer = KeywordTrainer()
    trainer.evaluate_keyword()

    # print(jellyfish.levenshtein_distance(str1, str2))
    # print(jellyfish.damerau_levenshtein_distance(str1, str2))
