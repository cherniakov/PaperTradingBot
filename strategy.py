import logging
import random

import backtrader as bt


class MinCommission(bt.CommInfoBase):
    params = (
        ('commission', 0.0005),
        ('min_commission', 50.0),
        ('commtype', bt.CommInfoBase.COMM_PERC),
        ('stocklike', True),
        ('percabs', True),
    )

    def _getcommission(self, size, price, pseudoexec):
        commission = abs(size) * price * self.p.commission
        return max(commission, self.p.min_commission)


class MyStrategy(bt.Strategy):
    """Тестовая стратегия со случайными сигналами"""
    
    params = (
        ('trade_history', None),
        ('initial_cash', None),
    )

    def __init__(self):
        self.logger = logging.getLogger('PaperTrading_Finam')
        self.live = False
        self.order = None
        self.trade_count = 0
    
    def start(self):
        # Восстанавливаем виртуальный портфель
        portfolio = self.p.trade_history.restore_portfolio(
            self.p.initial_cash
        )

        # Восстанавливаем свободные средства
        self.broker.setcash(float(portfolio['cash']))

        # Выводим свободные средства
        self.logger.info(
            f'Портфель | Свободные средства: {self.broker.getcash():,.2f} ₽'
        )

        # Восстанавливаем позиции
        for data in self.datas:
            symbol = data._name
            saved_position = portfolio['positions'].get(symbol)

            if saved_position is None:
                continue

            position = self.broker.getposition(data)

            position.set(
                saved_position['size'],
                float(saved_position['price'])
            )

            purchase_value = position.size * position.price
            short_symbol = symbol.split('.')[-1]

            self.logger.info(
                f'{short_symbol} | '
                f'Количество: {position.size} | '
                f'Средняя цена: {position.price:.2f} ₽ | '
                f'Стоимость покупки: {purchase_value:,.2f} ₽'
            )
              
    def next(self):
        if not self.live:
            return

        # Сохраняем стоимость виртуального портфеля
        cash = self.broker.getcash()
        equity = self.broker.getvalue()
        positions_value = equity - cash

        self.p.trade_history.save_equity(
            timestamp=bt.num2date(self.data.datetime[0]).isoformat(),
            cash=cash,
            positions_value=positions_value,
            initial_cash=self.p.initial_cash
        )
        # Счетчик кол-во сделок - для удобства тестирования
        if self.order or self.trade_count >= 4:
            return

        # Генерируем случайный сигнал
        signal = random.randint(0, 1)

        symbol = self.data._name.split('.')[-1]
        operation = 'BUY' if signal == 1 else 'SELL'

        if signal == 1:
            action = 'ПОКУПКА'
        elif self.position.size > 0:
            action = 'ПРОДАЖА'
        else:
            action = 'ПРОПУСК (нет акций)'

        self.logger.info(
            f'{symbol} | '
            f'Сигнал: {operation} | '
            f'Цена: {self.data.close[0]:.2f} ₽ | '
            f'Позиция: {self.position.size} | '
            f'Действие: {action}'
        )

        if signal == 1:
            self.order = self.buy()

        elif signal == 0 and self.position.size > 0:
            self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            
            self.p.trade_history.save_trade(
                timestamp=bt.num2date(order.executed.dt).isoformat(),
                symbol=order.data._name,
                short_name='Сбербанк',
                side='BUY' if order.isbuy() else 'SELL',
                quantity=abs(order.executed.size),
                price=order.executed.price,
                commission=order.executed.comm
                )
            
            self.trade_count += 1

            operation = 'BUY' if order.isbuy() else 'SELL'

            self.logger.info(
                f'{operation} | '
                f'Цена: {order.executed.price:.2f} | '
                f'Количество: {abs(order.executed.size)} | '
                f'Комиссия: {order.executed.comm:.2f} | '
                f'Сделка №{self.trade_count}'
            )

            if self.trade_count >= 4:
                self.logger.info('Исполнено 4 сделок. Останавливаем стратегию.')
                self.env.runstop()

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.logger.warning(
                'Заявка не исполнена: %s',
                order.getstatusname()
            )

        self.order = None

    def notify_data(self, data, status, *args, **kwargs):
        status_name = data._getstatusname(status)
        self.logger.info(status_name)

        if status == data.LIVE:
            self.live = True
            self.logger.info('Торговля в реальном времени разрешена')

        elif status in [data.DELAYED, data.DISCONNECTED]:
            self.live = False

    def stop(self):
        # Получаем итоговое состояние портфеля
        cash = self.broker.getcash()
        equity = self.broker.getvalue()
        positions_value = equity - cash

        # Сохраняем результат
        self.p.trade_history.save_equity(
            timestamp=bt.num2date(self.data.datetime[0]).isoformat(),
            cash=cash,
            positions_value=positions_value,
            initial_cash=self.p.initial_cash
        )

        # Выводим итоговое состояние
        self.logger.info(
            f'Итоговый портфель | '
            f'Свободные средства: {cash:,.2f} ₽ | '
            f'Стоимость позиций: {positions_value:,.2f} ₽ | '
            f'Капитал: {equity:,.2f} ₽ | '
            f'P&L: {equity - self.p.initial_cash:+,.2f} ₽'
        )
