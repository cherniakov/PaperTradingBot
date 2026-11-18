import csv
import os
from pathlib import Path
from uuid import uuid4
from decimal import Decimal


class TradeHistory:
    """Хранение истории исполненных виртуальных сделок"""

    def __init__(self, bot_id):
        # Папка для хранения истории конкретного робота
        root = Path(__file__).resolve().parent

        self.directory = root / 'TradingHistory' / bot_id
        self.directory.mkdir(parents=True, exist_ok=True)

        # Файл истории сделок
        self.file_path = self.directory / 'trades.csv'

        # Структура trades.csv
        self.fields = ['execution_id', 'timestamp', 'symbol', 'short_name', 
                       'side', 'quantity', 'price', 'commission']

        # Создаём файл, если его ещё нет
        if not self.file_path.exists() or self.file_path.stat().st_size == 0:
            with open(self.file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(self.fields)
        
        # Файл истории стоимости портфеля
        self.equity_path = self.directory / 'equity.csv'

        self.equity_fields = ['timestamp', 'cash', 'positions_value', 
                              'equity', 'pnl']

        if not self.equity_path.exists() or self.equity_path.stat().st_size == 0:
            with open(self.equity_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(self.equity_fields)

    def save_trade(self, timestamp, symbol, short_name, 
                   side, quantity, price, commission):
        """Сохранение исполненной сделки
        """

        trade = {
            'execution_id': str(uuid4()),
            'timestamp': timestamp,
            'symbol': symbol,
            'short_name': short_name,
            'side': side,
            'quantity': quantity,
            'price': price,
            'commission': round(commission, 2)
        }

        with open(self.file_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=self.fields)
            writer.writerow(trade)

            # Сбрасываем данные на диск
            file.flush()
            os.fsync(file.fileno())
            
    def load_trades(self):
        """Загрузка истории исполненных сделок"""

        trades = []

        with open(self.file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                trades.append(row)

        return trades

    def get_position(self, symbol):
        """Расчёт открытой позиции по инструменту"""

        position = 0

        trades = self.load_trades()

        for trade in trades:

            # Учитываем только нужный инструмент
            if trade['symbol'] != symbol:
                continue

            quantity = int(trade['quantity'])

            if trade['side'] == 'BUY':
                position += quantity

            elif trade['side'] == 'SELL':
                position -= quantity

        return position
    
    def get_cash(self, initial_cash):
        """Расчёт свободных денежных средств по истории сделок"""

        cash = Decimal(str(initial_cash))

        trades = self.load_trades()

        for trade in trades:
            quantity = Decimal(trade['quantity'])
            price = Decimal(trade['price'])
            commission = Decimal(trade['commission'])

            amount = quantity * price

            if trade['side'] == 'BUY':
                cash -= amount + commission

            elif trade['side'] == 'SELL':
                cash += amount - commission

            else:
                raise ValueError(
                    f"Неизвестная операция: {trade['side']}"
                )

        return cash
    
    def restore_portfolio(self, initial_cash):
        cash = Decimal(str(initial_cash))
        positions = {}
        realized_pnl = Decimal('0')

        trades = sorted(
            self.load_trades(),
            key=lambda trade: trade['timestamp']
        )

        for trade in trades:
            symbol = trade['symbol']
            side = trade['side']
            quantity = int(trade['quantity'])
            price = Decimal(trade['price'])
            commission = Decimal(trade['commission'])

            if quantity <= 0:
                raise ValueError(f'Некорректное количество: {quantity}')

            if symbol not in positions:
                positions[symbol] = {
                    'size': 0,
                    'price': Decimal('0')
                }

            position = positions[symbol]
            amount = quantity * price

            if side == 'BUY':
                total_cost = position['size'] * position['price'] + amount
                position['size'] += quantity
                position['price'] = total_cost / position['size']
                cash -= amount + commission
                realized_pnl -= commission

            elif side == 'SELL':
                if quantity > position['size']:
                    raise ValueError(
                        f'Продажа {quantity} акций {symbol} '
                        f'превышает открытую позицию '
                        f'{position["size"]}'
                    )

                profit = (price - position['price']) * quantity
                realized_pnl += profit - commission
                cash += amount - commission

                position['size'] -= quantity

                if position['size'] == 0:
                    position['price'] = Decimal('0')

            else:
                raise ValueError(f'Неизвестная операция: {side}')

        return {
            'cash': cash,
            'positions': positions,
            'realized_pnl': realized_pnl
        }

    def save_equity(self, timestamp, cash, positions_value, initial_cash):
        equity = cash + positions_value
        pnl = equity - initial_cash

        record = {
            'timestamp': timestamp,
            'cash': round(cash, 2),
            'positions_value': round(positions_value, 2),
            'equity': round(equity, 2),
            'pnl': round(pnl, 2)
        }

        # Загружаем существующие записи
        with open(self.equity_path, 'r', newline='', encoding='utf-8') as file:
            records = list(csv.DictReader(file))

        # Удаляем прежние записи с таким временем
        records = [
            row for row in records
            if row['timestamp'] != timestamp
        ]

        # Добавляем актуальное состояние
        records.append(record)

        # Записываем через временный файл
        temp_path = self.equity_path.with_suffix('.tmp')

        with open(temp_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(
                file,
                fieldnames=self.equity_fields
            )

            writer.writeheader()
            writer.writerows(records)

            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, self.equity_path)
