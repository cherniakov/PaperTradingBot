import json
from pathlib import Path

import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo  # ВременнАя зона

import backtrader as bt

from FinLabPy.Config import brokers, default_broker  # Все брокеры и брокер по умолчанию
from FinLabPy.Schedule.MOEX import Stocks  # Расписание торгов фондового рынка Московской Биржи
from FinLabPy.BackTrader import Store  # Хранилище BackTrader

from strategy import MyStrategy, MinCommission # Импорт стратегии из файла strategy
from trade_history import TradeHistory # Сохраняем историю сделок


if __name__ == '__main__':  # Точка входа при запуске этого скрипта
    dataname = 'TQBR.SBER'  # Тикер
    week_ago = date.today() - timedelta(days=7)  # Дата неделю назад без времени
    
    schedule = Stocks()  # Расписание биржи
    
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат сообщения
                        datefmt='%d.%m.%Y %H:%M:%S',  # Формат даты
                        level=logging.INFO,  # Уровень логируемых событий NOTSET/DEBUG/INFO/WARNING/ERROR/CRITICAL
                        handlers=[logging.FileHandler('PaperTrading_Finam.log', encoding='utf-8'), logging.StreamHandler()])  # Лог записываем в файл и выводим на консоль
    logging.Formatter.converter = lambda *args: datetime.now(tz=ZoneInfo('Europe/Moscow')).timetuple()  # В логе время указываем по МСК

    # Загружаем настройки торгового робота
    config_path = Path(__file__).resolve().parent / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)
    
    trade_history = TradeHistory(config['bot_id'])
 
    cerebro = bt.Cerebro(stdstats=False)  # Инициируем "движок" BackTrader. Стандартная статистика сделок и кривой доходности не нужна
    store = Store(broker=default_broker)  # Хранилище брокера по умолчанию
    # store = Store(broker=brokers['<Ключ словаря brokers из Config.py>'])  # Хранилище выбранного брокера

    # Настройки виртуального брокера из config.json
    cerebro.broker.setcash(config['initial_cash']) #начальный капитал
    cerebro.broker.addcommissioninfo(MinCommission(commission=config['commission'], 
                                                   min_commission=50.0)
                                     ) # ручная настройка коммиссии
    
    logging.info(f"Робот: {config['bot_id']} | Начальный капитал: {config['initial_cash']:,.2f} ₽ | Комиссия: {config['commission'] * 100:.3f}%")

    data = store.getdata(dataname=dataname, timeframe=bt.TimeFrame.Minutes, compression=1, fromdate=week_ago, live_bars=True)  # 3. Исторические и новые минутные бары за последнюю неделю по подписке
    # data = store.getdata(dataname=dataname, timeframe=bt.TimeFrame.Minutes, compression=1, fromdate=week_ago, live_bars=True, schedule=schedule)  # 4. Исторические и новые минутные бары за последнюю неделю по расписанию

    cerebro.adddata(data)  # Добавляем данные
    cerebro.addstrategy(MyStrategy, trade_history=trade_history, 
                        initial_cash=config['initial_cash'])  # Добавляем торговую систему
    cerebro.addsizer(bt.sizers.PercentSizerInt, percents=10) #Размер сделки 

    cerebro.run()  # Запуск торговой системы
