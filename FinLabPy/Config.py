# Курс Мультиброкер: Контроль https://finlab.vip/wpm-category/mbcontrol/

from FinamPy.FinamPy import FinamPy  # Провайдер Финам
from FinLabPy.Brokers.Finam import Finam  # Брокер Финам

# from TinvestPy.TinvestPy import TinvestPy  # Провайдер Т-Инвестиции
# from FinLabPy.Brokers.Tinvest import Tinvest  # Брокер Т-Инвестиции

# Провайдеры
fp_provider = FinamPy()  # Провайдер Финам
# tp_provider = TinvestPy()  # Провайдер Т-Инвестиции. Для демо счета TinkoffPy(demo=True). Курс Мультиброкер: Облигации https://finlab.vip/wpm-category/mbbonds/


# Брокеры
storage = 'file'  # Файловое хранилище
# storage = 'db'  # Курс Базы данных для трейдеров https://finlab.vip/wpm-category/databases/
brokers = {
    'Ф': Finam(code='Ф', name='Финам', provider=fp_provider, storage=storage),  # Финам
    # 'Ф2': Finam(code='Ф2', name='Финам', provider=fp_provider, account_id=1, storage=storage),  # Второй счет на Финам
    # 'Т': Tinvest(code='Т', name='Т-Инвестиции', provider=tp_provider, storage=storage),  # Т-Инвестиции
    # 'Т2': Tinvest(code='Т2', name='Т-Инвестиции', provider=tp_provider, account_id=1, storage=storage),  # Второй счет на Т-Инвестиции
}
# default_broker = brokers['Ф']  # Брокер по умолчанию для выполнения технических операций
default_broker = Finam(code='Ф', name='Финам', provider=fp_provider, storage=storage)
