# -*- coding: utf-8 -*-
import os
import sys
from collections import defaultdict
from dotenv import load_dotenv
from tinkoff.invest import Client
from tinkoff.invest.utils import quotation_to_decimal
import logging

# Настройка кодировки для Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Настройка логирования
logging.basicConfig(
    filename='portfolio_composition.log',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

load_dotenv()
TOKEN = os.getenv("TINKOFF_TOKEN")

def format_quantity(quantity):
    """Форматирование количества с разделителями тысяч"""
    return f"{quantity:,}".replace(",", " ")

def get_portfolio_composition(client):
    """Получение состава портфеля через API"""
    try:
        # Получаем список счетов
        accounts = client.users.get_accounts().accounts
        broker_account = next((acc for acc in accounts if acc.type == 1), None)
        
        if not broker_account:
            print("❌ Брокерский счет не найден")
            return None
            
        account_id = broker_account.id
        print(f"✅ Используем счет: {account_id}")
        
        # Получаем портфель
        portfolio = client.operations.get_portfolio(account_id=account_id)
        
        # Словарь для хранения позиций
        positions = defaultdict(lambda: {'quantity': 0, 'name': '', 'ticker': ''})
        
        # Обрабатываем позиции
        for position in portfolio.positions:
            if position.quantity.units > 0:  # Только активные позиции
                figi = position.figi
                quantity = position.quantity.units
                
                # Получаем информацию об инструменте
                try:
                    instrument = client.instruments.get_instrument_by(id_type=1, id=figi)
                    if instrument.instrument:
                        name = instrument.instrument.name
                        ticker = instrument.instrument.ticker
                        
                        positions[figi] = {
                            'quantity': quantity,
                            'name': name,
                            'ticker': ticker
                        }
                except Exception as e:
                    logging.error(f"Ошибка при получении информации об инструменте {figi}: {e}")
                    # Если не удалось получить через API, используем FIGI как тикер
                    positions[figi] = {
                        'quantity': quantity,
                        'name': 'Неизвестно',
                        'ticker': figi[:8]  # Первые 8 символов FIGI
                    }
        
        return positions
        
    except Exception as e:
        logging.error(f"Ошибка при получении портфеля: {e}")
        print(f"❌ Ошибка при получении портфеля: {e}")
        return None

def categorize_assets(positions):
    """Категоризация активов по типам"""
    bonds = {}
    stocks = {}
    etfs = {}
    others = {}
    
    for figi, data in positions.items():
        ticker = data['ticker']
        name = data['name']
        quantity = data['quantity']
        
        # Определяем тип актива по тикеру
        if ticker.startswith('RU000') or 'ОФЗ' in name or 'БО' in name:
            bonds[ticker] = {'name': name, 'quantity': quantity}
        elif ticker.startswith('T') and ('ETF' in name or 'фонд' in name):
            etfs[ticker] = {'name': name, 'quantity': quantity}
        elif len(ticker) <= 5 and not ticker.startswith('RU'):
            stocks[ticker] = {'name': name, 'quantity': quantity}
        else:
            others[ticker] = {'name': name, 'quantity': quantity}
    
    return bonds, stocks, etfs, others

def display_portfolio_composition(positions):
    """Отображение состава портфеля в нужном формате"""
    if not positions:
        print("❌ Нет данных для отображения")
        return
    
    print("📊 СОСТАВ ПОРТФЕЛЯ ЧЕРЕЗ API")
    print("=" * 80)
    print("Формат: $тикет; название; количество")
    print("=" * 80)
    
    # Категоризируем активы
    bonds, stocks, etfs, others = categorize_assets(positions)
    
    # Выводим облигации (сортировка по количеству от большего к меньшему)
    if bonds:
        print("\n📊 ОБЛИГАЦИИ:")
        print("-" * 80)
        # Сортируем облигации по количеству (от большего к меньшему)
        sorted_bonds = sorted(bonds.items(), key=lambda x: x[1]['quantity'], reverse=True)
        for ticker, data in sorted_bonds:
            print(f"${ticker}; {data['name']}; {format_quantity(data['quantity'])}")
    
    # Выводим акции (сортировка по количеству от большего к меньшему)
    if stocks:
        print("\n📈 АКЦИИ:")
        print("-" * 80)
        # Сортируем акции по количеству (от большего к меньшему)
        sorted_stocks = sorted(stocks.items(), key=lambda x: x[1]['quantity'], reverse=True)
        for ticker, data in sorted_stocks:
            print(f"${ticker}; {data['name']}; {format_quantity(data['quantity'])}")
    
    # Выводим ETF (сортировка по количеству от большего к меньшему)
    if etfs:
        print("\n📊 ETF:")
        print("-" * 80)
        # Сортируем ETF по количеству (от большего к меньшему)
        sorted_etfs = sorted(etfs.items(), key=lambda x: x[1]['quantity'], reverse=True)
        for ticker, data in sorted_etfs:
            print(f"${ticker}; {data['name']}; {format_quantity(data['quantity'])}")
    
    # Выводим прочие активы (сортировка по количеству от большего к меньшему)
    if others:
        print("\n🔍 ПРОЧИЕ АКТИВЫ:")
        print("-" * 80)
        # Сортируем прочие активы по количеству (от большего к меньшему)
        sorted_others = sorted(others.items(), key=lambda x: x[1]['quantity'], reverse=True)
        for ticker, data in sorted_others:
            print(f"${ticker}; {data['name']}; {format_quantity(data['quantity'])}")
    
    print("\n" + "=" * 80)
    
    # Статистика
    total_bonds = sum(data['quantity'] for data in bonds.values())
    total_stocks = sum(data['quantity'] for data in stocks.values())
    total_etfs = sum(data['quantity'] for data in etfs.values())
    total_others = sum(data['quantity'] for data in others.values())
    
    print(f"📊 Облигаций: {format_quantity(total_bonds)}")
    print(f"📈 Акций: {format_quantity(total_stocks)}")
    print(f"📊 ETF: {format_quantity(total_etfs)}")
    print(f"🔍 Прочих: {format_quantity(total_others)}")
    print(f"🎯 Всего активов: {len(positions)}")
    print(f"🎯 Общее количество: {format_quantity(total_bonds + total_stocks + total_etfs + total_others)}")

def main():
    """Основная функция"""
    if not TOKEN:
        print("❌ Не найден токен TINKOFF_TOKEN в переменных окружения")
        print("💡 Создайте файл .env с содержимым:")
        print("TINKOFF_TOKEN=ваш_токен_здесь")
        return
    
    print("🚀 Запуск анализа состава портфеля через API Tinkoff...")
    print(f"✅ Токен найден: {TOKEN[:10]}...")
    
    try:
        with Client(TOKEN) as client:
            print("✅ Подключение к API успешно")
            
            # Получаем состав портфеля
            positions = get_portfolio_composition(client)
            
            if positions:
                # Отображаем результат
                display_portfolio_composition(positions)
            else:
                print("❌ Не удалось получить данные портфеля")
                
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        print(f"❌ Критическая ошибка: {e}")
        print("💡 Проверьте:")
        print("   - Правильность токена")
        print("   - Доступность API Tinkoff")
        print("   - Наличие активных позиций в портфеле")

if __name__ == "__main__":
    main()
