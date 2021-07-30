# CSViewer
> simple and lightweight *.csv file viewer written in Python


![](screenshot.png)

## Installation

Windows:

```cmd
cd /d d:
git clone https://github.com/ma1ex/CSViewer.git
cd CSViewer
python -m venv venv && venv\scripts\activate
pip install -r requirements.txt
```

## Run application

Windows:

```cmd
cd /d d:\CSViewer
venv\scripts\activate
python main.py
```

## Features

> _Rus_: 
> - Быстрая загрузка больших файлов
> - Закрашивание нечетных строк "зеброй"
> - Отображение общего количества строк и столбцов
> - Автоопределение кодировки* (utf-8, cp1251, cp866, koi8-r)
> - Выбор разделителя значений - запятая, точка с запятой, табуляция
> - Автоподбор ширины столбцов при двойном клике на заголовке
> - Копирование в буфер обмена значения выбранной ячейки

## Dependencies
> wxPython

### Requirements
> - Python >= 3.6

## Compiling to binaries

Windows:

```cmd
cd /d d\CSViewer:
python -m venv venv && venv\scripts\activate
pip install -r requirements_dev.txt
python setup_wx.py build
```

After compilation in the project directory will appear `build_csviewer_win_x64`

## Run compiled application

Windows:

```cmd
build_csviewer_win_x64\CSViewer.exe
```

## Release History

* 1.0.0
    * Release v1.0.0

## Contributing

1. Fork it (<https://github.com/ma1ex/CSViewer/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push main feature/fooBar`)
5. Create a new Pull Request

## License

Distributed under the MIT license.
