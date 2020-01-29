# Standard Libraries
from collections import deque
import shutil
import random
import threading

# 3rd Party Libraries
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon
from PyQt5.QtCore import Qt
import keyboard

# Custom Libraries
from ui import initUI
from staticmethods import *  # is_connected, notify, make_directory, image_name, popup, apply_config, monitor_resolution
from reddit_connect import *  # sub_exists, image_download_execute
from repeated_timer import RepeatedTimer


class MainWindow(QMainWindow):

    width, height = monitor_resolution()
    image_list = []

    def __init__(self):
        QMainWindow.__init__(self)
        initUI(self)
        make_directory()
        self.deque()

        keyboard.add_hotkey('ctrl+right', self.next_action_fn)
        keyboard.add_hotkey('ctrl+left', self.previous_action_fn)
        keyboard.add_hotkey('ctrl+up', self.favourite_action_fn)
        keyboard.add_hotkey('ctrl+down', self.download_thread)

        try:
            self.set_image = self.image_list[0]
            self.display_image_label(self.image_list[0])
        except IndexError:
            self.set_blank()

    def set_blank(self):

        text = 'Directory Empty' \
               '<hr><p><span style="font-size: 18px; margin-top= 50px">Download images by clicking "Download"<br>OR<br>Add images manually</span></p>' \
               '<hr><p><span style="font-size: 13px">* You can manually add images in "downloaded" or "favourites" folder*</span></p>'
        default_css = 'QLabel#viewingArea {font-size: 30px; padding-top: 50px; color: white; background: black;}'
        self.image_label.setText(f'{text}')
        self.image_label.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.image_label.setStyleSheet(f'{default_css}')

    def deque(self):
        self.image_list = deque(image_name())

    def previous_image(self):
        if self.image_list:
            self.image_list.rotate(1)
            try:
                self.display_image_label(self.image_list[0])
                self.set_image = self.image_list[0]
            except FileNotFoundError:
                self.set_blank()
                self.deque()

    def next_image(self):
        if self.image_list:
            self.image_list.rotate(-1)
            try:
                self.display_image_label(self.image_list[0])
                self.set_image = self.image_list[0]
            except FileNotFoundError:
                self.set_blank()
                self.deque()

    def add_to_favs(self):
        if self.image_list:
            main_path = os.path.realpath(os.getcwd())
            source_path = os.path.join(os.sep, main_path, self.set_image)
            if self.set_image.split('\\')[0] == 'downloaded':
                shutil.move(source_path, dst=os.path.join(os.sep, main_path, 'favourites'))
                notify("Added to favourites !", " ")

            else:
                notify("Already in favourites \u2764", " ")

            self.image_list.popleft()
            self.image_list.insert(0, os.path.join('favourites', self.set_image.split('\\')[1]))
            self.set_image = self.image_list[0]

    def download_images(self):
        total_image = self.listWidget.count()
        notify(f'Download started \u0085{total_image*5} images will be downloaded', " ")
        before = dict([(f, None) for f in os.listdir('downloaded')])
        image_download_execute(get_config('sub-list'))  # runs the threaded module in reddit_connect.py
        after = dict([(f, None) for f in os.listdir('downloaded')])
        added = [f for f in after if f not in before]
        notify(f'Download Successful : {len(added)} added to downloaded', " ")
        to_extend = []
        for file in added:
            to_extend.append(os.path.join('downloaded', file))
        # print(to_extend)
        self.image_list.extend(to_extend)

    def download_thread(self):
        threading.Thread(target=self.download_images).start()

    def shuffle_images(self):
        if get_config('shuffle-images'):
            random.shuffle(self.image_list)
        else:
            self.deque()

    def cbox_state(self, cbox):
        """affects how checkbox interacts with GUI"""
        if cbox.text() == "Download":
            if cbox.isChecked() == 1:
                if "downloaded" not in dirs:
                    dirs.append('downloaded')
                    self.deque()
            else:
                dirs.remove('downloaded')
                self.deque()
                self.fav_cbox.setChecked(True)

        if cbox.text() == "Favourites":
            if cbox.isChecked() == 1:
                if "favourites" not in dirs:
                    dirs.append('favourites')
                    self.deque()
            else:
                dirs.remove('favourites')
                self.deque()
                self.download_cbox.setChecked(True)

        if cbox.text() == "Activate System Tray":
            if cbox.isChecked() == 1:
                apply_config('activate-system-tray', True)
            else:
                apply_config('activate-system-tray', False)

        if cbox.text() == "Auto-Changer":
            if cbox.isChecked() == 1:
                apply_config('auto-change', True)
                notify("Auto Changer Enabled", " ")
            else:
                apply_config('auto-change', False)
                self.start_auto_changer()

        if cbox.text() == "Run at Startup":
            if cbox.isChecked() == 1:
                apply_config('startup', True)
            else:
                apply_config('startup', False)

        if cbox.text() == "Shuffle Images":
            if cbox.isChecked() == 1:
                apply_config('shuffle-images', True)
                self.shuffle_images()
            else:
                apply_config('shuffle-images', False)
                self.shuffle_images()

    def combobox_apply(self):
        if get_config('auto-change'):
            try:
                value = int(self.change_every_value.text())
            except ValueError:
                self.change_every_value.clear()
                return print('Invalid entry !')
            if value > 1000:
                print('Exceeds value !')
                self.change_every_value.clear()
            else:
                apply_config('change-every', value)
                apply_config('time-format', self.change_every_combobox.currentText())

            self.start_auto_changer()
            self.comboBox_apply_btn.hide()

    def display_image_label(self, image_file):
        if self.image_list:
            scaled_image = QPixmap(image_file).scaled(600, 338, Qt.KeepAspectRatio, Qt.FastTransformation)
            if not scaled_image.isNull():
                self.image_label.setPixmap(scaled_image)
            else:
                changed_image_file = image_file.split('.')[0]+'.png'
                os.rename(image_file, changed_image_file)
                self.image_list[0] = changed_image_file
                image_file = changed_image_file
                scaled_image = QPixmap(image_file).scaled(600, 338, Qt.KeepAspectRatio, Qt.FastTransformation)
                self.image_label.setPixmap(scaled_image)

    def set_as_wallpaper(self):
        if self.image_list:
            notify("Wallpaper Changed !", " ")
            main_path = os.path.realpath(os.getcwd())
            wallpaper_path = os.path.join(os.sep, main_path, self.set_image)
            SPI_SETDESKWALLPAPER = 0x0014

            ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER,
                                                       0,
                                                       ctypes.c_wchar_p(wallpaper_path),
                                                       3)

    '''----------------------------------- SYSTEM TRAY FUNCTION CALLS ---------------------------------------------'''

    def next_action_fn(self):
        self.next_image()
        self.set_as_wallpaper()

    def shuffle_action_fn(self):
        self.shuffle_images()
        self.shuffle_cbox.setChecked(True)
        apply_config('shuffle-images', True)

    def previous_action_fn(self):
        self.previous_image()
        self.set_as_wallpaper()

    def favourite_action_fn(self):
        self.add_to_favs()

    def download_action_fn(self):
        self.download_thread()

    @staticmethod
    def open_action_fn():
        window.showNormal()

    '''---------------------------------  END OF SYSTEM TRAY FUNCTION CALLS ------------------------------------'''

    def addsub_to_list(self):
        if is_connected():
            if len(get_config('sub-list')) <= 5:
                if self.addsub.text() != '' and sub_exists(self.addsub.text()):
                    self.listWidget.addItem(self.addsub.text())
                    data = get_config('sub-list')
                    data.append(self.addsub.text())
                    apply_config('sub-list', data)
                    self.addsub.setText('')
                    self.setFocus()
                else:
                    popup('Popup', 'Subreddit : <b><span style="color:red">{}</span></b> doesn\'t exists !'.format(self.addsub.text()))
                    self.addsub.clear()
                    self.addsub.clearFocus()
            else:
                popup('Popup', 'Maximum subreddit reached !<br>Remove existing to add.')

        else:
            popup('Popup', 'Check your internet connection')

    def remove_sub(self):
        data = get_config('sub-list')
        data.remove(self.listWidget.currentItem().text())
        apply_config('sub-list', data)
        self.listWidget.takeItem(self.listWidget.currentRow())

    def clear_sub(self):
        apply_config('sub-list', [])
        self.listWidget.clear()

    def closeEvent(self, event):
        if self.systray_cbox.isChecked() == 1:
            event.ignore()
            self.tray_icon.show()
            self.hide()
        else:
            try:
                self.initiate_background.stop()
                notify("Auto Changer Disabled", " ")
            except AttributeError:
                pass

    def tray_icon_doubleclick(self, event):
        if event == QSystemTrayIcon.DoubleClick:
            self.show()

    def start_auto_changer(self):
        if get_config('auto-change'):
            numeric_value = get_config('change-every')
            time_format = get_config('time-format')
            if time_format == 'minutes':
                time = numeric_value*60
            elif time_format == 'hours':
                time = numeric_value*60*60
            else:
                time = numeric_value*60*60*60
            self.initiate_background = RepeatedTimer(time, self.next_action_fn)
            self.initiate_background.start()
            notify("Auto Changer Activated",
                   f"Time has been set to {get_config('change-every')} {get_config('time-format')}")
        else:
            try:
                self.initiate_background.stop()
                notify("Auto Changer Disabled", " ")
                self.comboBox_apply_btn.show()
            except AttributeError:
                pass


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showNormal()
    sys.exit(app.exec_())