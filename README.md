# CSViewer
> simple and lightweight *.csv file viewer written in Python


![](screenshot_1.png)
![](screenshot_2.png)

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

> _Eng_:
> - Fast loading of large files;
> - Zebra shading of odd lines;
> - Display the total number of rows and columns;
> - Autodetection* and manual selection of encoding (utf-8, cp1251, cp866, koi8-r);
> - Separator selection - comma, semicolon, tabulation;
> - Auto column width selection with double click on header;
> - Copying the value of the selected cell to the clipboard;
> 
> _Rus_: 
> - Быстрая загрузка больших файлов;
> - Закрашивание нечетных строк "зеброй";
> - Отображение общего количества строк и столбцов;
> - Автоопределение* и ручной выбор кодировки (utf-8, cp1251, cp866, koi8-r);
> - Выбор разделителя значений - запятая, точка с запятой, табуляция;
> - Автоподбор ширины столбцов при двойном клике на заголовке;
> - Копирование в буфер обмена значения выбранной ячейки;

## Dependencies
> wxPython

### Requirements
> - Python >= 3.6

## Compiling to binaries

Windows:

```cmd
cd /d d\CSViewer:
venv\scripts\activate
pip install -r requirements_dev.txt
python setup_wx.py build
```

After compilation in the project directory will appear `Build\CSViewer_vX.X.X_win_x64`

## Run compiled application

Windows:

```cmd
Build\CSViewer_vX.X.X_win_x64\CSViewer.exe
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

Distributed under the MIT license. See ``LICENSE.md`` for more information.
