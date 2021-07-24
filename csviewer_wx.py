import csv
import time
from datetime import datetime
import os
from pprint import pprint

import wx
import wx.grid
import wx.lib.agw.pybusyinfo as pbi

import images


class Log:

    def __init__(self):

        self.show_debug = True
        self.show_info = True
        self.show_warning = True
        self.show_error = True
        self.show_print = True

        # File writer
        self.write_debug = False
        self.write_info = False
        self.write_warning = False
        self.write_error = False

        self.log_file_name = 'app.log'

    def debug(self, *args, **kwargs):

        if self.show_debug:
            print('DEBUG:    ', *args, **kwargs)

    def info(self, *args, **kwargs):

        if self.show_info:
            print('INFO:     ', *args, **kwargs)

    def warning(self, *args, **kwargs):

        if self.show_warning:
            print('WARNING:  ', *args, **kwargs)

    def error(self, *args, **kwargs):

        if self.show_error:
            print('ERROR:    ', *args, **kwargs)

    def print(self, *args, **kwargs):

        if self.show_print:
            print(*args, **kwargs)

    def pprint(self, message):

        if self.show_print:
            pprint(message)


class AppConfig:
    APP_VERSION = '1.0.0'
    APP_NAME = 'CSViewer'
    APP_DESCRIPTION = 'Simple and faster csv viewer'
    APP_SINCE = '2020.11'
    APP_RELEASE = '2020.11'
    AUTHOR = 'Matvienko Alexey (ma1ex)'
    AUTHOR_CONTACTS = 'develop2biz@gmail.com'
    WX_VERSION = wx.VERSION


class CsvApp(Log, AppConfig):

    def __init__(self):
        Log.__init__(self)

        # wx App
        self.app = wx.App()

        # App config -----------------------------------------------------------
        self.window_title = f'{AppConfig.APP_NAME} v{AppConfig.APP_VERSION}'
        self.window_size = (700, 450)

        # CSV file settings ----------------------------------------------------
        self.csv_file = None  # File name and path
        self.csv_encoding = 'utf-8'
        self.csv_delimiter = ';'
        self.csv_file_size = 0
        self.preview_fragment: bytes
        self.preview_encoding_text: wx.TextCtrl

        # Widgets --------------------------------------------------------------
        self.main_frame = wx.Frame(parent=None)        # Main Frame
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)     # Sizer
        self.menu_bar = wx.MenuBar()                   # Menu Bar
        self.toolbar = wx.ToolBar()                    # Toolbar TODO: как лучше сделать?
        self.status_bar = None                         # StatusBar TODO: как лучше сделать?
        self.csv_grid = wx.grid.Grid(self.main_frame)  # Grid Widget
        self.text_total_rows: wx.TextCtrl              # TextCtrl for Total Grid rows
        self.text_total_cols: wx.TextCtrl              # TextCtrl for Total Grid cols

        # self.timer = wx.Timer(self.main_frame)
        self.timer: wx.Timer            # Global Timer
        self.time_current = 0           # Snapshot current timestamp
        self.clock_splash: wx.TextCtrl  # TextCtrl for Splash
        self.gauge_splash: wx.Gauge     # For tests

        # Grid settings
        self.total_rows = 0  # Общее количество строк
        self.total_cols = 0  # Общее количество столбцов
        self.font = wx.Font(wx.FontInfo(10))  # Шрифт для ячеек
        self.is_zebra = False  # Закрашивание нечетных строк в таблице

    # UI -----------------------------------------------------------------------

    def create_app_ui(self):

        # Main Frame
        self.create_main_frame()

        # Main menu
        self.create_menu()

        # StatusBar
        self.create_status_bar()

        # Toolbar
        self.create_toolbar()

        # Csv grid
        self.create_grid_ui()

        # Sizer
        self.create_main_sizer()

    def create_main_frame(self):
        self.main_frame.SetTitle(self.window_title)
        self.main_frame.SetClientSize(self.window_size)
        self.main_frame.SetIcon(images.csviewer_wand_ico_16.GetIcon())
        self.main_frame.Centre()
        self.main_frame.Show(show=True)

        # Events
        # self.main_frame.Bind(wx.EVT_CLOSE, self.on_exit)  # Событие закрытия главного окна
        self.main_frame.Bind(wx.EVT_TIMER, self.on_timer)  # Глобальный таймер

    def create_main_sizer(self):
        self.main_sizer.Add(self.toolbar, proportion=0, flag=wx.EXPAND | wx.RIGHT | wx.LEFT, border=3)
        # self.main_sizer.Add((5, 5), 0)
        self.main_sizer.Add(self.csv_grid, proportion=1, flag=wx.EXPAND | wx.ALL, border=3)

        # Apply Sizer
        self.main_frame.SetSizer(self.main_sizer)

        # Redraw
        # self.main_sizer.Fit(self.main_frame)

    def create_menu(self):

        # Menu "File" ----------------------------------------------------------
        menu_file = wx.Menu()
        # Items
        item_open = menu_file.Append(wx.ID_ANY, item='&Открыть\tCTRL+O', helpString='')
        item_open.SetBitmap(images.folder_open_png_16.GetBitmap())

        menu_file.AppendSeparator()

        item_exit = menu_file.Append(wx.ID_EXIT, item='&Выход\tCTRL+Q', helpString='')
        item_exit.SetBitmap(images.exit_png_16.GetBitmap())

        # Menu "About" ---------------------------------------------------------
        menu_about = wx.Menu()
        # Items
        item_about = menu_about.Append(wx.ID_ABOUT, 'О программе')
        item_about.SetBitmap(images.question_png_16.GetBitmap())

        # Добавление пунктов меню в основной менюбар
        self.menu_bar.Append(menu=menu_file, title='&Файл')
        self.menu_bar.Append(menu=menu_about, title='&Помощь')

        # Add menu item in MenuBar
        self.main_frame.SetMenuBar(menuBar=self.menu_bar)

        # Events
        self.main_frame.Bind(wx.EVT_MENU, self.on_open, item_open)
        self.main_frame.Bind(wx.EVT_MENU, self.on_about, item_about)
        self.main_frame.Bind(wx.EVT_MENU, self.on_exit, item_exit)

    def create_toolbar(self):
        self.toolbar = wx.ToolBar(self.main_frame, style=wx.TB_HORIZONTAL)

        font11 = wx.Font(wx.FontInfo(11))
        font11.SetWeight(wx.FONTWEIGHT_BOLD)
        font14 = wx.Font(wx.FontInfo(14))

        label_rows = wx.StaticText(self.toolbar, -1, 'Строк:')
        label_rows.SetFont(font11)

        label_cols = wx.StaticText(self.toolbar, -1, 'Столбцов:')
        label_cols.SetFont(font11)

        # text_total_rows = wx.StaticText(self.toolbar, -1, f'[ {self.get_grid_info()[0]} ]')
        # self.text_total_rows = wx.StaticText(self.toolbar, -1, f'[ {self.total_rows} ]')

        self.text_total_rows = wx.TextCtrl(self.toolbar, -1)
        self.text_total_rows.SetEditable(False)
        self.text_total_rows.SetSize(90, 28)
        self.text_total_rows.SetFont(font14)
        self.text_total_rows.SetForegroundColour('#0D47A1')
        self.text_total_rows.SetBackgroundColour('#F0F0F0')
        self.text_total_rows.SetValue(str(self.total_rows))

        self.text_total_cols = wx.TextCtrl(self.toolbar, -1)
        self.text_total_cols.SetEditable(False)
        self.text_total_cols.SetSize(90, 28)
        self.text_total_cols.SetFont(font14)
        self.text_total_cols.SetForegroundColour('#FF6D00')
        self.text_total_cols.SetBackgroundColour('#F0F0F0')
        self.text_total_cols.SetValue(str(self.total_cols))

        # Checkbox
        # ch_zebra = wx.CheckBox(self.toolbar, -1, 'Отобразить "зебру"')
        # ch_zebra.Disable()

        self.toolbar.AddSeparator()
        # Open
        tool_open_item = self.toolbar.AddTool(wx.ID_ANY, '',
                                              wx.Bitmap(images.folder_open.GetBitmap()),
                                              shortHelp='Открыть файл')
        # Переключатель "зебры"
        # self.toolbar.AddSeparator()
        # self.toolbar.AddControl(ch_zebra, 'ch_zebra')

        # TEST Buttons ---------------------------------------------------------
        # self.toolbar.AddSeparator()
        # tool_test = self.toolbar.AddTool(wx.ID_ANY, '', wx.Bitmap(images.blue_square_png_16.GetBitmap()),
        #                                  shortHelp='TEST: Показать Splash')
        # tool_test2 = self.toolbar.AddTool(wx.ID_ANY, '', wx.Bitmap(images.blue_square_png_16.GetBitmap()),
        #                                  shortHelp='TEST: file preloader')
        # ----------------------------------------------------------------------

        # Контролы отображения кол-ва строк и стобцов
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddControl(label_rows, 'label_rows')
        self.toolbar.AddControl(self.text_total_rows, 'text_total_rows')
        self.toolbar.AddSeparator()
        self.toolbar.AddControl(label_cols, 'label_cols')
        self.toolbar.AddControl(self.text_total_cols, 'text_total_cols')
        self.toolbar.AddSeparator()

        self.toolbar.Realize()

        # Events ---------------------------------------------------------------
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open, tool_open_item)  # Open file
        # self.toolbar.Bind(wx.EVT_CHECKBOX, self.on_grid_check_zebra, ch_zebra)

        # TEST
        # self.toolbar.Bind(wx.EVT_TOOL, self.on_show_splash, tool_test)
        # self.toolbar.Bind(wx.EVT_TOOL, lambda message: self.show_error_dialog('sfsfsdf', None), tool_test)
        # self.toolbar.Bind(wx.EVT_TOOL, self.create_preloader_dialog, tool_test2)

    def create_status_bar(self):

        self.status_bar = self.main_frame.CreateStatusBar()
        self.status_bar.SetFieldsCount(4)

        # self.status_bar.SetMinHeight(35)
        # self.status_bar.SetStatusWidths([400, 250, 100, 250])

        # Абсолютная величина отрицательного целого указывает относительный
        # размер поля, выраженный количеством отводимых полю частей в общей
        # ширине панели. Например, вызов statusbar.SetStatusWidth([-1, -2, -3])
        # отводит для самого правого поля половину ширины (3/6 части), центральная
        # область получает треть ширины (2/6 части), а крайнее левое поле получает
        # шестую часть ширины (1/6 часть).
        self.status_bar.SetStatusWidths([-4, -2, -1, -2])
        self.status_bar.SetStatusText('Нажмите кнопку "Открыть" на панели для загрузки файла', 0)

        # Попытка отобразить картинку в Statubar-е
        # # img = wx.Image()
        # rect = self.status_bar.GetFieldRect(3)
        # self.debug(rect.x, rect.y)
        # # rect.x = 16
        # # rect.y += 1
        # img = wx.StaticBitmap(self.status_bar, wx.ID_ANY, images.hourglass_png_16.GetBitmap(), size=(16, 16))
        # img.SetPosition([rect.x, rect.y + 2])
        # # self.status_bar.SetStatusText(images.hourglass_png_16.GetBitmap(), 3)

    def create_grid_ui(self):

        self.csv_grid.CreateGrid(35, 20)

        # Глобальные настройки для Grid
        # self.attr_line = wx.grid.GridCellAttr()
        # self.attr_line.SetBackgroundColour('#F5FDC1')
        self.csv_grid.SetDefaultCellAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
        # self.csv_grid.SetDefaultCellFont(self.font)
        self.csv_grid.SetDefaultCellFont(wx.Font(wx.FontInfo(11)))
        self.csv_grid.SetDefaultRowSize(28)
        self.csv_grid.SetDefaultCellTextColour('#000030')

        # self.csv_grid.LabelBackgroundColour = '#FFFD9F'
        self.csv_grid.LabelBackgroundColour = '#FAFAA4' # FAFAA4 - светлее | FBFBB0 - темнее  # EEF78A | E6DB74
        self.csv_grid.SetGridLineColour('#AAAAAA')
        self.csv_grid.LabelFont = wx.Font(wx.FontInfo(10).Bold())
        self.csv_grid.LabelTextColour = '#682714'
        # self.csv_grid.LabelTextColour = '#004960'

        # Events
        self.csv_grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_DCLICK, self.on_grid_col_autosize)
        self.csv_grid.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.on_grid_context_menu)
        # self.csv_grid.Bind(wx.EVT_CONTEXT_MENU, self.on_grid_context_menu)

    # def create_preloader_dialog(self, e):
    #
    #     self.debug(':create_preloader_dialog: self.csv_file >', self.csv_file)
    #
    #     # Dialog Frame ---------------------------------------------------------
    #     preloader_frame = wx.Dialog(
    #         parent=self.main_frame,
    #         id=-1,
    #         title='Настройки файла перед загрузкой',
    #         size=(600, 322)
    #     )
    #     preloader_frame.SetIcon(images.switch_png_16.GetIcon())
    #     preloader_frame.CenterOnParent()
    #
    #     # Auto decoding for first load -----------------------------------------
    #     try:
    #         preview_fragment = self.preview_fragment.decode()
    #     except UnicodeDecodeError as err:
    #         self.error(':create_preloader_dialog:', err)
    #         preview_fragment = self.preview_fragment.decode('cp1251')
    #         self.csv_encoding = 'cp1251'
    #
    #     #
    #     label_1 = wx.StaticText(preloader_frame, -1, 'Кодировка файла:', pos=(20, 15))
    #     encoding_choice = wx.Choice(preloader_frame, -1, pos=(20, 40), size=(140, 30),
    #                                 choices=['utf-8', 'cp1251', 'cp866', 'koi8-r'])
    #     # encoding_choice.SetSelection(0)
    #     encoding_choice.SetSelection(self.on_preloader_load_encoding())
    #     # self.csv_encoding = encoding_choice.GetString(0)
    #     self.debug(':create_preloader_dialog: self.csv_encoding >', self.csv_encoding)
    #
    #     # self.preview_fragment = self.csv_file_preview()
    #     # self.csv_file_preview()
    #
    #     # preview_fragment = self.preview_fragment
    #
    #     self.preview_encoding_text = wx.TextCtrl(preloader_frame, -1, '',
    #                                 pos=(170, 39), size=(400, 150), style=wx.TE_MULTILINE | wx.TE_READONLY)
    #     # self.preview_encoding_text.SetValue(str(self.preview_fragment))
    #     self.preview_encoding_text.SetValue(preview_fragment)
    #
    #     label_2 = wx.StaticText(preloader_frame, -1, 'Разделитель:', pos=(20, 210))
    #     delimiter_choice = wx.Choice(preloader_frame, -1, pos=(170, 205), size=(250, 30),
    #                                 choices=['Точка с запятой', 'Запятая', 'Знак табуляции'])
    #     # delimiter_choice.SetSelection(0)
    #     delimiter_choice.SetSelection(self.on_preloader_load_delimiter())
    #
    #     # Buttons --------------------------------------------------------------
    #     # pos(left, top)
    #     btn_ok = wx.Button(preloader_frame, -1, 'OK', pos=(410, 250))
    #     btn_ok.SetBitmap(images.confirm_png_16.Bitmap, wx.LEFT)
    #     btn_ok.SetBitmapMargins((2, 2))
    #     btn_ok.SetInitialSize()
    #     btn_ok.SetDefault()
    #
    #     btn_cancel = wx.Button(preloader_frame, -1, 'Отмена', pos=(490, 250))
    #     btn_cancel.SetBitmap(images.cancel_png_16.Bitmap, wx.LEFT)
    #     btn_cancel.SetBitmapMargins((2, 2))
    #     btn_cancel.SetInitialSize()
    #
    #     # Events ---------------------------------------------------------------
    #     def on_close_self(e):
    #         preloader_frame.Close()
    #         self.make_grid_table()
    #
    #     preloader_frame.Bind(wx.EVT_CHOICE, self.on_preloader_encoding, encoding_choice)
    #     preloader_frame.Bind(wx.EVT_CHOICE, self.on_preloader_delimiter, delimiter_choice)
    #     preloader_frame.Bind(wx.EVT_BUTTON, on_close_self, btn_ok)
    #     preloader_frame.Bind(wx.EVT_BUTTON, lambda e: preloader_frame.Close(), btn_cancel)
    #
    #     preloader_frame.ShowModal()

    def create_preloader_dialog(self, e):

        self.debug(':create_preloader_dialog: self.csv_file >', self.csv_file)

        # Dialog Frame ---------------------------------------------------------
        preloader_frame = wx.Dialog(
            parent=self.main_frame,
            id=-1,
            title='Настройки файла перед загрузкой',
            size=(600, 448)
        )
        preloader_frame.SetIcon(images.switch_png_16.GetIcon())
        preloader_frame.CenterOnParent()

        # Auto decoding for first load -----------------------------------------
        try:
            preview_fragment = self.preview_fragment.decode()
        except UnicodeDecodeError as err:
            self.error(':create_preloader_dialog:', err)
            preview_fragment = self.preview_fragment.decode('cp1251')
            self.csv_encoding = 'cp1251'
        # preview_fragment = 'Test text' * 20

        # Шрифт некоторых значений пунктов
        font = wx.Font(wx.FontInfo(11).Bold())
        # Calculate file size
        orig_size, _, format_size = self.convert_bytes(os.path.getsize(self.csv_file))

        box_main = wx.BoxSizer(wx.VERTICAL)

        # 0 File name ----------------------------------------------------------
        box_fname = wx.BoxSizer(wx.HORIZONTAL)

        label_fname = wx.StaticText(preloader_frame, -1, 'Имя файла:')
        label_fname.SetForegroundColour('navy')

        value_fname = wx.StaticText(preloader_frame, -1, f' {os.path.basename(self.csv_file)} ')
        value_fname.SetFont(font)

        box_fname.Add(label_fname)
        box_fname.Add((87, 0), 0)
        box_fname.Add(value_fname)

        # 1. File size ---------------------------------------------------------
        box_fsize = wx.BoxSizer(wx.HORIZONTAL)

        label_fsize = wx.StaticText(preloader_frame, -1, 'Размер файла:')
        label_fsize.SetForegroundColour('navy')

        if orig_size >= 50000000:
            value_fsize = wx.StaticText(preloader_frame, -1, f' {format_size} ')
            value_fsize.SetForegroundColour('#C11E1E')
            value_fsize.SetFont(font)

            desc_ico = wx.StaticBitmap(preloader_frame, -1, images.warn_circle_red_16.Bitmap)
            desc_ico.SetToolTip('Очень большой размер файла!\n'
                                'Может существенно снизится производительность и отзывчивость программы!')

        elif 50000000 > orig_size >= 20000000:
            value_fsize = wx.StaticText(preloader_frame, -1, f' {format_size} ')
            value_fsize.SetForegroundColour('#C1B23F')
            value_fsize.SetFont(font)

            # desc_ico = wx.StaticBitmap(preloader_frame, -1, images.warn_circle_yellow_16.Bitmap)
            desc_ico = wx.StaticBitmap(preloader_frame, -1, images.warn_triangle_yellow_16.Bitmap)
            desc_ico.SetToolTip('Большой размер файла!\n'
                                'Может снизится производительность программы!')

        else:
            value_fsize = wx.StaticText(preloader_frame, -1, f' {format_size} ')
            value_fsize.SetForegroundColour('#3DA346')
            value_fsize.SetFont(font)

            # desc_ico = wx.StaticBitmap(preloader_frame, -1, images.confirm_circle_16.Bitmap)
            desc_ico = wx.StaticBitmap(preloader_frame, -1, images.confirm_16.Bitmap)
            desc_ico.SetToolTip('Размер файла в пределах нормы!')

        box_fsize.Add(label_fsize)
        box_fsize.Add((72, 0), 0)
        box_fsize.Add(value_fsize)
        box_fsize.Add(desc_ico)

        # 2. File preview ------------------------------------------------------
        box_preview = wx.BoxSizer(wx.HORIZONTAL)

        label_1 = wx.StaticText(preloader_frame, -1, 'Кодировка файла:')
        label_1.SetForegroundColour('navy')

        encoding_choice = wx.Choice(preloader_frame, -1, size=(140, 30),
                                    choices=['utf-8', 'cp1251', 'cp866', 'koi8-r'])
        encoding_choice.SetSelection(self.on_preloader_load_encoding())
        self.debug(':create_preloader_dialog: self.csv_encoding >', self.csv_encoding)


        self.preview_encoding_text = wx.TextCtrl(preloader_frame, -1, '',
                                    size=(400, 150), style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.preview_encoding_text.SetBackgroundColour('#F5FDC1')
        self.preview_encoding_text.SetValue(preview_fragment)

        box_preview.Add(encoding_choice)
        box_preview.Add((19, 0), 0)
        box_preview.Add(self.preview_encoding_text)

        # 3. Delimiter ---------------------------------------------------------
        box_delimiter = wx.BoxSizer(wx.HORIZONTAL)

        label_2 = wx.StaticText(preloader_frame, -1, 'Разделитель:')
        label_2.SetForegroundColour('navy')

        delimiter_choice = wx.Choice(preloader_frame, -1, size=(250, 30),
                                    choices=['Точка с запятой', 'Запятая', 'Знак табуляции'])
        delimiter_choice.SetSelection(self.on_preloader_load_delimiter())

        box_delimiter.Add(label_2)
        box_delimiter.Add((87, 0), 0)
        box_delimiter.Add(delimiter_choice)

        # 4. Zebra -------------------------------------------------------------
        box_zebra = wx.BoxSizer(wx.HORIZONTAL)

        label_zebra = wx.StaticText(preloader_frame, -1, 'Закрашивать нечетные\nстроки:', size=(150, 30))
        label_zebra.SetForegroundColour('navy')

        ch_zebra = wx.CheckBox(preloader_frame, -1)

        if orig_size >= 50000000:
            ch_zebra.Disable()
            zebra_ico = wx.StaticBitmap(preloader_frame, -1, images.warn_circle_red_16.Bitmap)
            zebra_ico.SetToolTip('При очень большом размере файла эта функция\n'
                                'может существенно снизить производительность программы!')

        elif 50000000 > orig_size >= 20000000:
            # zebra_ico = wx.StaticBitmap(preloader_frame, -1, images.warn_circle_yellow_16.Bitmap)
            zebra_ico = wx.StaticBitmap(preloader_frame, -1, images.warn_triangle_yellow_16.Bitmap)
            zebra_ico.SetToolTip('При большом размере файла\n'
                                'используйте с осторожностью, т.к.\n'
                                'может снизится производительность программы!')

        else:
            zebra_ico = wx.StaticBitmap(preloader_frame, -1)

        box_zebra.Add(label_zebra)
        box_zebra.Add((9, 0), 0)
        box_zebra.Add(ch_zebra)
        box_zebra.Add(zebra_ico)

        # 5. Buttons -----------------------------------------------------------
        buttons_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)

        # pos(left, top)
        btn_ok = wx.Button(preloader_frame, -1, 'OK')
        btn_ok.SetBitmap(images.confirm_16.Bitmap, wx.LEFT)
        btn_ok.SetBitmapMargins((3, 3))
        btn_ok.SetInitialSize()
        btn_ok.SetDefault()

        btn_cancel = wx.Button(preloader_frame, -1, 'Отмена')
        btn_cancel.SetBitmap(images.cancel_png_16.Bitmap, wx.LEFT)
        btn_cancel.SetBitmapMargins((3, 3))
        btn_cancel.SetInitialSize()

        buttons_sizer.Add(btn_ok)
        buttons_sizer.Add(btn_cancel)

        # Frame sizer ----------------------------------------------------------
        box_main.Add((0, 10), 0)  # (width, height)
        box_main.Add(box_fname, proportion=0, flag=wx.RIGHT | wx.LEFT, border=10)
        box_main.Add((0, 20), 0)
        box_main.Add(box_fsize, proportion=0, flag=wx.RIGHT | wx.LEFT, border=10)
        box_main.Add((0, 20), 0)
        box_main.Add(label_1, proportion=0, flag=wx.RIGHT | wx.LEFT, border=10)
        box_main.Add((0, 10), 0)
        box_main.Add(box_preview, proportion=0, flag=wx.RIGHT | wx.LEFT, border=10)
        box_main.Add((0, 10), 0)
        box_main.Add(box_delimiter, proportion=0, flag=wx.RIGHT | wx.LEFT, border=10)
        box_main.Add((0, 20), 0)
        box_main.Add(box_zebra, proportion=0, flag=wx.RIGHT | wx.LEFT, border=10)
        box_main.Add((0, 20), 0)
        box_main.Add(buttons_sizer, proportion=0, flag=wx.RIGHT | wx.LEFT | wx.ALIGN_RIGHT, border=10)
        preloader_frame.SetSizer(box_main)

        # Events ---------------------------------------------------------------
        def on_close_self(e):
            """
            Закрытие текущего модального окна вызов метода создания таблицы и выполнение
            подготовительных настроек

            :param e: объект события
            :return:
            """

            # preloader_frame.Close()
            preloader_frame.Destroy()

            if not ch_zebra.IsChecked():
                self.is_zebra = False

            self.preview_fragment = None

            self.make_grid_table()

        def on_check_zebra(e):
            """
            Событие включения/отключения "зебры" для таблицы

            :param e: объект события
            :return:
            """

            if e.IsChecked():
                self.is_zebra = True

            else:
                self.is_zebra = False

        preloader_frame.Bind(wx.EVT_CHOICE, self.on_preloader_encoding, encoding_choice)
        preloader_frame.Bind(wx.EVT_CHOICE, self.on_preloader_delimiter, delimiter_choice)
        preloader_frame.Bind(wx.EVT_CHECKBOX, on_check_zebra, ch_zebra)
        preloader_frame.Bind(wx.EVT_BUTTON, on_close_self, btn_ok)
        preloader_frame.Bind(wx.EVT_BUTTON, lambda e: preloader_frame.Close(), btn_cancel)

        preloader_frame.ShowModal()

    def show_error_dialog(self, message, e=None):

        wx.Bell()
        dlg = wx.MessageDialog(
            parent=None,
            caption='ERROR!',
            message=message,
            style=wx.OK | wx.ICON_ERROR)

        dlg.ShowModal()
        dlg.Destroy()

    # Methods ------------------------------------------------------------------

    # def create_csv_grid(self, csv_file: str, encoding='utf-8', delimiter=';'):
    #
    #     # Удаление предыдущей таблицы, если она есть, перед вставкой новой
    #     self.remove_csv_grid()
    #     self.csv_grid.EnableEditing(False)
    #
    #     # Локальные настройки для Grid
    #     # font10 = wx.Font(wx.FontInfo(10))
    #     # font10 = wx.Font(11, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    #     attr_row = wx.grid.GridCellAttr()
    #     attr_row.SetBackgroundColour('#F5FDC1')
    #
    #     # attr_row_font = wx.grid.GridCellAttr()
    #     # attr_row_font.SetFont(font10)
    #
    #     row_counter = 0
    #
    #     try:
    #         start_time = datetime.now()
    #
    #         with open(csv_file, 'r', encoding=encoding) as f:
    #             reader = csv.reader(f, delimiter=delimiter)
    #
    #             # self.on_show_splash(None)
    #             self.status_bar.SetStatusText('Загружается файл...', 3)
    #
    #             # Получение 1-й строки из CSV-файла - это заголовки
    #             headers = reader.__next__()
    #
    #             # Определение кол-ва колонок и сразу же их создания - AppendCols()
    #             # self.AppendCols(len(headers) - 1)
    #             self.csv_grid.AppendCols(len(headers))
    #             self.total_cols = len(headers)
    #
    #             # Вставка первой строки CSV-файла как заголовков колонок
    #             for i, col in enumerate(headers):
    #                 self.csv_grid.SetColLabelValue(i, col)
    #
    #             # Вставка значение построчно и поколоночно
    #             # for i, row in enumerate(reader, 1):
    #             for i, row in enumerate(reader):
    #
    #                 # Динамическое создание строки перед вставкой
    #                 self.csv_grid.AppendRows(1)
    #                 self.csv_grid.SetRowSize(i, 25)
    #                 row_counter = i
    #
    #                 # # Зебра на каждую нечетную строку
    #                 if i % 2 != 0:
    #                     self.csv_grid.SetRowAttr(i, attr_row)
    #
    #                     # IncRef() - вот избежание ошибки:
    #                     # C++ assertion "m_count > 0" failed in wxRefCounter::DecRef(): invalid ref data count
    #                     attr_row.IncRef()
    #
    #                 # self.csv_grid.SetRowAttr(i, attr_row_font)
    #                 # attr_row_font.IncRef()
    #
    #                 for j, item in enumerate(row):
    #                     self.csv_grid.SetCellValue(i, j, item)
    #                     # self.csv_grid.SetCellFont(i, j, font10)  # TODO: Такое нельзя применять - виснет комп !!!
    #                     # self.csv_grid.SetCellAlignment(i, j, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
    #
    #             yield reader
    #
    #         end_load_time = datetime.now() - start_time
    #         self.debug('> :create_csv_grid: > Elapsed load time:', end_load_time)
    #
    #         self.total_rows = row_counter + 1
    #
    #         # Update status
    #         self.status_bar.SetStatusText(f'Двойной клик на заголовке столбца для автоподбора ширины', 0)
    #         self.status_bar.SetStatusText(f'Кодировка: {encoding.upper()} | Разделитель: {delimiter}', 1)
    #         editable = 'Режим редактирования' if self.csv_grid.IsEditable() else 'Режим чтения'
    #         self.status_bar.SetStatusText(editable, 2)
    #         self.status_bar.SetStatusText(f'Файл загружен: OK! [{end_load_time}]', 3)
    #
    #         self.text_total_rows.SetValue(str(self.total_rows))
    #         self.text_total_cols.SetValue(str(self.total_cols))
    #
    #     except Exception as err:
    #         self.error('> :create_grid: >', err)
    #
    #     else:
    #         self.debug('> :create_grid: > OK!')

    def make_grid_table(self):

        # Общий список для загрузки всего CSV-файла
        items_list = []

        try:
            self.status_bar.SetStatusText('Загружается файл...', 3)
            busy_splash = pbi.PyBusyInfo(message='Загружается файл, подождите...',
                                         parent=self.main_frame, title='Чтение файла',
                              icon=images.clock_remain_png_16.GetBitmap())
            wx.Yield()

            start_time = datetime.now()

            # Чтение файла
            with open(self.csv_file, 'r', encoding=self.csv_encoding) as f:
                reader = csv.reader(f, delimiter=self.csv_delimiter)

                for item in reader:
                    items_list.append(item)

            self.debug('> :create_csv_grid: > items_list len:', len(items_list))
            self.debug('> :create_csv_grid: > items_list headers len:', len(items_list[0]))
            self.debug('> :create_csv_grid: > items_list preview:', items_list[:2])

            self.total_rows = len(items_list) - 1
            self.total_cols = len(items_list[0])

            self.text_total_rows.SetValue(str(self.total_rows))
            self.text_total_cols.SetValue(str(self.total_cols))

            # Удаление предыдущей таблицы, если она есть, перед вставкой новой
            self.remove_grid_table()
            # Предварительное создание пустых строк и столбцов на основе полученных значений
            self.csv_grid.AppendRows(self.total_rows)
            self.csv_grid.AppendCols(self.total_cols)
            # Readonly flag
            self.csv_grid.EnableEditing(False)

            # Создание "зебры" -------------------------------------------------

            self.debug(':create_csv_grid: > self.is_zebra:', self.is_zebra)
            if self.is_zebra:  # Глобальный атрибут
                attr_row = wx.grid.GridCellAttr()
                attr_row.SetBackgroundColour('#F5FDC1')  # olive

                # Зебра на каждую нечетную строку
                for i in range(self.total_rows):
                    if i % 2 != 0:
                        self.csv_grid.SetRowAttr(i, attr_row)

                        # IncRef() - вот избежание ошибки:
                        # C++ assertion "m_count > 0" failed in wxRefCounter::DecRef(): invalid ref data count
                        attr_row.IncRef()

            # Вставка значений -------------------------------------------------

            # Вставка первой строки CSV-файла как заголовков колонок
            for i, col in enumerate(items_list[0]):
                self.csv_grid.SetColLabelValue(i, col)

            # Вставка значение построчно и поколоночно, начиная с 1-го значения общего списка
            # [[self.csv_grid.SetCellValue(i, j, item) for j, item in enumerate(row)] for i, row in enumerate(items_list[1:])]

            for i, row in enumerate(items_list[1:]):

                # Зебра на каждую нечетную строку | TODO: перевести в атрибут объекта
                # if i % 2 != 0:
                #     self.csv_grid.SetRowAttr(i, attr_row)
                #
                #     # IncRef() - вот избежание ошибки:
                #     # C++ assertion "m_count > 0" failed in wxRefCounter::DecRef(): invalid ref data count
                #     attr_row.IncRef()

                # Вставка значений для одной строки
                for j, item in enumerate(row):
                    self.csv_grid.SetCellValue(i, j, item)

            end_load_time = datetime.now() - start_time

            # Очистка памяти и освобождение ресурсов
            items_list.clear()
            del busy_splash

            self.debug('> :create_csv_grid: > File load time:', end_load_time)
            self.debug('> :create_csv_grid: > items_list len after clear:', len(items_list))

            # Update status
            self.status_bar.SetStatusText(f'Двойной клик на заголовке столбца для автоподбора ширины', 0)
            self.status_bar.SetStatusText(f'Кодировка: {self.csv_encoding.upper()} | Разделитель: {self.csv_delimiter}', 1)
            editable = 'Режим редактирования' if self.csv_grid.IsEditable() else 'Режим чтения'
            self.status_bar.SetStatusText(editable, 2)
            self.status_bar.SetStatusText(f'Файл загружен: OK! [{end_load_time}]', 3)

        except Exception as err:
            self.error('> :create_grid: >', err)

        else:
            self.debug('> :create_grid: > OK!')

    def remove_grid_table(self):
        if self.csv_grid is not None:
            rows = self.csv_grid.GetNumberRows()
            cols = self.csv_grid.GetNumberCols()

            if rows > 0:
                self.csv_grid.DeleteRows(0, rows)
            if cols > 0:
                self.csv_grid.DeleteCols(0, cols)

    def csv_file_preview(self):

        try:
            with open(self.csv_file, 'rb') as f:
                d = f.read()

            # return d[:400]
            self.preview_fragment = d[:300]

        except Exception as err:
            self.error(':csv_file_preview:', err)

    def convert_bytes(self, size) -> tuple:
        """
        This method will convert bytes to MB.... GB... etc
        """

        orig_size = round(size)
        calc_size = 0.0
        format_size = ''

        for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:

            if size < 1024.0:
                calc_size = round(size, 1),
                format_size = '%3.1f %s' % (size, x)
                break

            size /= 1024.0

        return orig_size, calc_size, format_size

    # Events -------------------------------------------------------------------

    def on_preloader_encoding(self, e):

        encoding = e.GetString()

        self.debug('> :on_preloader_encoding: Choice encoding >', encoding)

        self.csv_encoding = encoding
        self.debug('> :on_preloader_encoding: Get global encoding >', self.csv_encoding)

        # if self.preview_fragment[0:3] == b'\xef\xbb\xbf':

        # reload_fragment = self.csv_file_preview()
        try:
            reload_fragment = self.preview_fragment.decode(self.csv_encoding)
            self.preview_encoding_text.SetValue(reload_fragment)

        except UnicodeDecodeError as err:
            self.error(':on_preloader_encoding:', err)
            self.show_error_dialog('Файл не в UTF-8 кодировке!')
        # except AttributeError as err:
        #     self.error(':csv_file_preview:', err)

    def on_preloader_load_encoding(self):

        encoding = self.csv_encoding

        # 'utf-8', 'cp1251', 'cp866', 'koi8-r'
        if encoding == 'utf-8':
            return 0
        elif encoding == 'cp1251':
            return 1
        elif encoding == 'cp866':
            return 2
        elif encoding == 'koi8-r':
            return 3

    def on_preloader_delimiter(self, e):

        delimiter = e.GetString()

        # 'Точка с запятой', 'Запятая', 'Знак табуляции'
        if delimiter == 'Точка с запятой':
            delimiter = ';'

        elif delimiter == 'Запятая':
            delimiter = ','

        elif delimiter == 'Знак табуляции':
            delimiter = '\t'

        self.debug('> :on_preloader_delimiter: Choice delimiter >', delimiter)

        self.csv_delimiter = delimiter
        self.debug('> :on_preloader_delimiter: Get global delimiter >', self.csv_delimiter)

    def on_preloader_load_delimiter(self) -> int:

        delimiter = self.csv_delimiter

        # 'Точка с запятой', 'Запятая', 'Знак табуляции'
        if delimiter == ';':
            return 0
        elif delimiter == ',':
            return 1
        elif delimiter == '\t':
            return 2

    def on_grid_context_menu(self, e):

        cell_value = self.csv_grid.GetCellValue(row=e.GetRow(), col=e.GetCol())
        self.debug('> :on_grid_context_menu: value >', cell_value)

        ctx = wx.Menu()
        item = ctx.Append(wx.NewIdRef(), 'Копировать значение в буфер обмена')
        item.SetBitmap(images.document_copy_png_16.GetBitmap())
        ctx.Bind(wx.EVT_MENU, lambda h: self.on_grid_copy_cell_value(cell_value, e), item)
        self.csv_grid.PopupMenu(ctx)
        ctx.Destroy()

        e.Skip()

    def on_grid_check_zebra(self, e):

        # self.debug(':on_grid_check_zebra: CheckBox "zebra" status >', e.IsChecked())

        total_rows = self.csv_grid.GetNumberRows()
        # self.debug(':on_grid_check_zebra: Total grid rows >', total_rows)

        # Локальные настройки для Grid
        default_bg = self.csv_grid.GetBackgroundColour()
        # self.debug(':on_grid_check_zebra: Default background >', default_bg)

        # font10 = wx.Font(wx.FontInfo(10))
        # font10 = wx.Font(11, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        attr_row = wx.grid.GridCellAttr()
        attr_row.SetBackgroundColour('#F5FDC1')  # olive
        # attr_row.SetBackgroundColour('#BCE6EF')

        arrt_default = wx.grid.GridCellAttr()
        arrt_default.SetBackgroundColour('#FFFFFF')

        if e.IsChecked():
            # Зебра на каждую нечетную строку | TODO: перевести в атрибут объекта
            for i in range(total_rows):
                if i % 2 != 0:
                    self.csv_grid.SetRowAttr(i, attr_row)

                    # IncRef() - вот избежание ошибки:
                    # C++ assertion "m_count > 0" failed in wxRefCounter::DecRef(): invalid ref data count
                    attr_row.IncRef()
            self.csv_grid.Refresh()

        else:
            for i in range(total_rows):
                if i % 2 != 0:
                    self.csv_grid.SetRowAttr(i, arrt_default)
                    arrt_default.IncRef()
            # self.csv_grid.SetDefaultCellBackgroundColour((255, 255, 255, 255))

            self.csv_grid.Refresh()

    def on_grid_col_autosize(self, e):
        # print(evt.GetRow(), evt.GetCol(), evt.GetPosition())
        try:
            self.csv_grid.AutoSizeColumn(e.GetCol())
        except Exception as err:
            self.warning(':on_grid_col_autosize: Клик по строке, а не по колонке >', err)

        e.Skip()

    def on_grid_copy_cell_value(self, value, e):
        self.debug('> :on_grid_copy_cell: value >', value)

        self.set_clipboard(value)

        e.Skip()

    def set_clipboard(self, data: str):
        self.debug('> :set_clipboard: > data:', data, len(data), bool(data))

        if data:
            clipdata = wx.TextDataObject()
            clipdata.SetText(data)
            wx.TheClipboard.Open()
            success = wx.TheClipboard.SetData(clipdata)
            wx.TheClipboard.Close()
            self.debug('> :set_clipboard: > Clipboard set data success:', success)

            if success:
                self.status_bar.SetStatusText('Скопировано в буфер обмена!', 3)

        else:
            self.status_bar.SetStatusText('Нельзя скопировать пустое значение!', 3)

        # Проверка скопированных данных
        # text_data = wx.TextDataObject()
        # if wx.TheClipboard.Open():
        #     success = wx.TheClipboard.GetData(text_data)
        #     wx.TheClipboard.Close()
        # if success:
        #     self.debug('Clipboard data:', text_data.GetText())

    def on_show_splash(self, e):

        # splash_frame = wx.Frame(parent=self.main_frame, id=-1, title='Test dialog', size=(400, 250))

        # splash_frame = wx.Dialog(parent=self.main_frame, id=-1, title='Test dialog', size=(400, 250),
        #                          style=wx.FRAME_TOOL_WINDOW)
        splash_frame = wx.Dialog(parent=self.main_frame, id=-1, title='Test dialog', size=(400, 250))
        splash_frame.CenterOnParent()

        box = wx.BoxSizer(wx.VERTICAL)

        # panel = wx.Panel(splash_frame, -1)

        # self.clock_splash = wx.TextCtrl(splash_frame, -1, '', (110, 40), (150, 25))
        self.clock_splash = wx.TextCtrl(splash_frame, -1, '', size=(330, 40))

        # self.gauge_splash = wx.Gauge(splash_frame, -1, 75, (75, 100), (250, 30))
        self.gauge_splash = wx.Gauge(splash_frame, -1, 100, size=(250, 40))

        # btn_timer_start = wx.Button(splash_frame, -1, 'Start', (40, 150), (60, 30))
        btn_timer_start = wx.Button(splash_frame, -1, 'Start')
        # btn_timer_stop = wx.Button(splash_frame, -1, 'Stop', (120, 150), (60, 30))
        btn_timer_stop = wx.Button(splash_frame, -1, 'Stop')
        # btn = wx.Button(splash_frame, -1, 'Close me!', (300, 150), (60, 30))
        btn = wx.Button(splash_frame, -1, 'Close me!')

        splash_frame.Bind(wx.EVT_BUTTON, lambda e: splash_frame.Destroy(), btn)

        box.Add((10, 10), 0)
        box.Add(self.clock_splash, proportion=0, flag=wx.CENTER | wx.RIGHT | wx.LEFT, border=3)
        box.Add((10, 10), 0)
        box.Add(self.gauge_splash, proportion=0, flag=wx.EXPAND | wx.RIGHT | wx.LEFT, border=20)
        box.Add(btn_timer_start)
        box.Add(btn_timer_stop)
        box.Add(btn)

        splash_frame.SetSizer(box)

        # self.main_frame.Bind(wx.EVT_TIMER, self.on_timer)
        splash_frame.Bind(wx.EVT_BUTTON, self.on_timer_start, btn_timer_start)
        splash_frame.Bind(wx.EVT_BUTTON, self.on_timer_stop, btn_timer_stop)

        splash_frame.ShowModal()
        # splash_frame.Show(True)

    def on_timer(self, e):
        self.gauge_splash.Pulse()

        # t = time.localtime(time.time())
        # st = time.strftime("%H:%M:%S", t)
        # self.clock.SetValue(st)

        # t = time.localtime(time.time())
        t = time.time() - self.time_current
        # t = datetime.now()
        # diff = t - self.cur_time
        # self.debug(type(diff))
        # self.clock.SetValue(f'{diff}')
        diff = datetime.utcfromtimestamp(t).strftime('%H:%M:%S:%f')
        self.clock_splash.SetValue(f'Загружается ... {diff}')
        # self.status_bar.PushStatusText(f'Загружается ... {diff}', 3)

        # self.clock.SetValue(datetime.fromtimestamp(t).strftime("%H:%M:%S"))

    def on_timer_start(self, e):

        self.timer = wx.Timer(self.main_frame)
        self.time_current = time.time()
        self.timer.Start(100)

        self.debug('> :on_timer: Timer status >', 'worked' if self.timer.IsRunning() else 'stopped')

    def on_timer_stop(self, e):

        if self.timer:
            self.gauge_splash.SetValue(100)
            self.timer.Stop()

            self.debug('> :on_timer_stop: Timer status >', 'worked' if self.timer.IsRunning() else 'stopped')

            self.time_current = 0
            self.timer = None

        else:
            self.debug('> :on_timer_stop: Timer status >', self.timer)

    def on_open(self, e):
        self.debug('> :on_open: get EventID:', e.GetId())

        open_dialog = wx.FileDialog(
            parent=None,
            message='Выберите файл для открытия',
            defaultDir=os.getcwd(),
            defaultFile='',
            wildcard='*.csv',
            style=wx.FD_OPEN,
        )

        if open_dialog.ShowModal() == wx.ID_OK:
            self.debug('> :on_open: get Path:', open_dialog.GetPath())

            self.status_bar.SetStatusText('', 0)
            self.csv_file = open_dialog.GetPath()
            self.main_frame.SetTitle(f'{AppConfig.APP_NAME} v{AppConfig.APP_VERSION} - {open_dialog.GetPath()}')

            # Preloader and config
            self.csv_file_preview()
            self.create_preloader_dialog(None)

    def on_about(self, e):
        self.debug('> :on_about: get EventID:', e.GetId())

        wx.Bell()
        wx.MessageDialog(parent=None,
                         caption=f'About "{AppConfig.APP_NAME} - {AppConfig.APP_VERSION}"',
                         message=f'AppName: {AppConfig.APP_NAME}\n'
                                 f'Description: {AppConfig.APP_DESCRIPTION}\n'
                                 f'Version: {AppConfig.APP_VERSION}\n'
                                 f'wxVersion: {AppConfig.WX_VERSION}\n'
                                 f'Since Date: {AppConfig.APP_SINCE}\n'
                                 f'Release Date: {AppConfig.APP_RELEASE}\n\n'
                                 f'Author: {AppConfig.AUTHOR}\n'
                                 f'Contacts: {AppConfig.AUTHOR_CONTACTS}',
                         style=wx.OK | wx.ICON_INFORMATION).ShowModal()

    def on_exit(self, e):
        self.debug('> :on_exit: get EventID:', e.GetId())

        dlg = wx.MessageDialog(parent=None,
                               caption='Выход из программы',
                               message='Вы уверены, что хотите закрыть программу?',
                               style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        # Show modal dialog
        res = dlg.ShowModal()
        self.debug('> :on_exit: get result:', res)

        if res == wx.ID_YES:
            self.main_frame.Destroy()

        else:
            dlg.Close()

    # Proposals ----------------------------------------------------------------
    # def load_config(self, file='config.json'):
    #     """
    #     Open and Read JSON App Config
    #     :param file:
    #     :return:
    #     """
    #
    #     if os.path.exists(file) and os.path.isfile(file):
    #         f = open(file, 'r', encoding='utf-8')
    #         raw = f.read()
    #         f.close()
    #         parsed = re.sub(r'\n^\s*//.+$', '', raw, flags=re.MULTILINE)
    #         # print(parsed)
    #         return json.loads(parsed)
    #
    #         # with open(file, 'r', encoding='utf-8') as read_file:
    #         # parsed = re.sub(r'\n^\s*//.+$', '', read_file, flags=re.MULTILINE)
    #         # return json.load(read_file)
    #     else:
    #         # Default settings
    #         return {
    #             "path_snippets": ".",
    #             "tab_width": 4
    #         }

    # App run ------------------------------------------------------------------
    def run(self):
        # App UI
        self.create_app_ui()

        # # Activate App
        self.app.MainLoop()
