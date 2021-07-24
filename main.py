from datetime import datetime

from csviewer_wx import CsvApp


def main():
    # Program timer
    start_time = datetime.now()
    print('Starting...')

    try:
        # app = wx.App()
        # # Отображение окна программы
        # wnd = MainWindow(
        #     title='My Super wxPython program! I am cool Haцker!',
        #     size=(1000, 700)
        # )
        # wnd.Show(show=True)
        #
        # # Запуск основного цикла программы
        # app.MainLoop()

        app = CsvApp()
        app.window_size = (1000, 700)
        app.run()

    except KeyboardInterrupt:
        print()
        print('WARNING: Прервано пользователем!')

    except Exception as err:
        print()
        print('ERROR: ', err)

    finally:
        # LOG: ---------------------------------------------------------------------
        print()
        print('Report:', '*' * 40)
        print('    Start time:', start_time.strftime('%d.%m.%Y %H:%M:%S'))
        print('    End time:', datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
        print('    Elapsed time:', datetime.now() - start_time)
        print('*' * 48)


if __name__ == '__main__':
    main()
