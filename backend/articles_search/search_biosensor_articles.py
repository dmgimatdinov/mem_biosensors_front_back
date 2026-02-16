#!/usr/bin/env python3
"""
Инструмент для структурирования и форматирования научных статей о биосенсорах
по ГОСТ Р 7.0.100–2018 на основе результатов поиска в Scopus/WoS.

Использование:
  1. Экспортируйте результаты поиска из Scopus/WoS в CSV или BibTeX.
  2. Заполните данные вручную в список articles ниже.
  3. Запустите скрипт: python3 search_biosensor_articles.py
"""

from dataclasses import dataclass
from typing import List, Optional
import json

@dataclass
class BiosensorArticle:
    """Структура для хранения метаданных научной статьи о биосенсорах."""
    authors: List[str]  # Список авторов (фамилия, инициалы)
    title: str
    journal: str
    year: int
    volume: str
    number: str
    pages: str
    doi: str
    url: str
    annotation: str  # 4–5 предложений
    source: str  # "Scopus" или "Web of Science"
    
    def format_gost(self) -> str:
        """Форматирование по ГОСТ Р 7.0.100–2018."""
        authors_str = ", ".join(self.authors)
        gost = (
            f"{authors_str} {self.title} // {self.journal}. – {self.year}. – "
            f"Т. {self.volume}, № {self.number}. – С. {self.pages}. – "
            f"DOI: {self.doi}."
        )
        return gost
    
    def format_output(self) -> str:
        """Полный формат вывода с аннотацией."""
        output = f"""
{'='*80}
СТАТЬЯ {self.source}
{'='*80}

БИБЛИОГРАФИЧЕСКОЕ ОПИСАНИЕ (ГОСТ Р 7.0.100–2018):
{self.format_gost()}

АННОТАЦИЯ:
{self.annotation}

ССЫЛКА:
https://doi.org/{self.doi}
{self.url}

"""
        return output


def search_strategy() -> str:
    """Возвращает рекомендуемые поисковые запросы для Scopus и WoS."""
    return """
РЕКОМЕНДОВАННЫЕ ПОИСКОВЫЕ ЗАПРОСЫ:

1. SCOPUS (Advanced Search):
   TITLE-ABS-KEY((biosensor* OR "bio-sensor*") 
     AND (design OR "design method*" OR "design system" OR framework OR modelling 
          OR modeling OR "digital twin" OR "machine learning") 
     AND (performance OR sensitivity OR "limit of detection" OR reproducib* 
          OR accuracy OR cost OR "time to develop" OR "development time"))
     AND PUBYEAR > 2019 AND PUBYEAR < 2026
     AND LIMIT-TO(DOCTYPE,"ar")

2. WEB OF SCIENCE (Advanced Search):
   TS=(biosensor* AND (design OR "design method*" OR framework OR modelling 
       OR modeling OR "digital twin" OR "machine learning") 
       AND (performance OR sensitivity OR "limit of detection" OR reproducib* 
            OR accuracy OR cost OR "time to develop"))
       AND Document Types=Article
       AND Publication Years=2020-2025

ФИЛЬТРЫ:
  • Document Type: Article (только рецензируемые журнальные статьи)
  • Years: 2020–2025
  • Экспорт полей: авторы, заголовок, журнал, год, том, номер, страницы, DOI, URL
  • Приоритет: Open Access статьи

РЕЛЕВАНТНЫЕ ЖУРНАЛЫ:
  • Biosensors and Bioelectronics
  • ACS Sensors
  • Analytical Chemistry
  • Sensors and Actuators B: Chemical
  • Talanta
"""


def main():
    print("ИНСТРУМЕНТ ДЛЯ ПОИСКА И ФОРМАТИРОВАНИЯ НАУЧНЫХ СТАТЕЙ О БИОСЕНСОРАХ")
    print("="*80)
    print(search_strategy())
    print("\nИНСТРУКЦИИ:")
    print("""
1. Перейдите на сайт Scopus (scopus.com) или Web of Science (webofscience.com)
2. Используйте поисковые запросы выше
3. Отфильтруйте результаты по документам типа "Article" (2020–2025)
4. Экспортируйте результаты (минимум 10–15 статей для отбора)
5. Заполните данные в этом скрипте или подготовьте CSV-файл
6. Запустите: python3 search_biosensor_articles.py --format

СЛЕДУЮЩИЕ ШАГИ:
  • Отправьте список найденных DOI в этот чат
  • Или загрузите CSV-файл с метаданными
  • Я подготовлю полный отформатированный список по ГОСТ с аннотациями
""")


if __name__ == "__main__":
    main()