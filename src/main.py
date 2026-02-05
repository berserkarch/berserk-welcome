import gi
import sys
import threading
import subprocess
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

base_dir = os.path.dirname(os.path.abspath(__file__))


class Handler:
    def __init__(self, builder):
        self.builder = builder
        self.window = builder.get_object("main_window")
        self.get_widgets()
        self.setup_dynamic_widgets()

    def get_widgets(self):
        widget_ids = [
            "label_notify",
            "button_easy_install",
            "button_adv_install",
            "button_mirrors",
            "button_gparted",
            "label_welcome_message",
            "hbox_util_buttons",
            "hbox_install_buttons",
            "hbox_footer_buttons",
            "label_info",
            "label_info_header1",
            "easy_install_btn_label",
            "adv_install_btn_label",
            "image_logo",
        ]

        [setattr(self, i, self.builder.get_object(i)) for i in widget_ids]

    def setup_dynamic_widgets(self):
        self.easy_install_btn_label.set_markup("<b>Offline Install</b>")
        self.adv_install_btn_label.set_markup("<b>Online Install </b>")
        self.image_logo.set_from_file(os.path.join(base_dir, "images/berserkarch.png"))

        desc = (
            "A bleeding-edge, security centric Arch-based Linux Distribution.\n"
            "Crafted with hackers, developers, and nerds alike in mind.\n"
        )
        self.label_info.set_markup(desc)
        self.window.show_all()

    def on_main_window_destroy(self):
        Gtk.main_quit()

    def on_button_clicked(self, widget, command: list, message: str):
        self.label_notify.set_markup(f"<b>{message}...</b>")
        self.run_cmd(command)

    def on_easy_install_clicked(self, widget):
        self.label_notify.set_markup("Running the Installer...")
        cmd = "sudo cp /etc/calamares/settings_offline.conf /etc/calamares/settings.conf && calamares -D9 | tee -a /home/liveuser/berserkarch-install.log"
        self.run_cmd([cmd], shell=True)
        
    def on_adv_install_clicked(self, widget):
        self.label_notify.set_markup("Running the Installer...")
        cmd = "sudo cp /etc/calamares/settings_online.conf /etc/calamares/settings.conf && calamares -D9 | tee -a /home/liveuser/berserkarch-install.log"
        self.run_cmd([cmd], shell=True)

    def on_gp_clicked(self, widget):
        self.on_button_clicked(widget, ["sudo", "gparted"], "Launching GParted...")

    def on_mirror_clicked(self, widget):
        self.label_notify.set_markup("<b>Updating mirrors...</b>")
        cmd = "sudo pipx install btweak --global --force && btweak fix --gpg"
        self.run_cmd([cmd], shell=True)

    def on_quit_clicked(self, widget):
        self.window.get_application().quit()

    def launch_advanced_installer_dialog(self, install_method):
        builder = Gtk.Builder()
        try:
            builder.add_from_file(os.path.join(base_dir, "NotifyAction.glade"))
        except GLib.Error as e:
            print(f"FATAL: Could not load NotifyAction.glade: {e}")
            return

        dialog = builder.get_object("notify_action_dialog")
        label_title = builder.get_object("label_title_message")
        label_title.set_markup(f"<b>{install_method} is Coming Soon...</b>")
        builder.connect_signals(DialogHandler(dialog, self.label_notify))
        dialog.set_transient_for(self.window)
        dialog.run()
        dialog.destroy()

    def run_cmd(self, cmd_array, shell=False):
        def _run():
            print(f"THREAD: Running command: {cmd_array}")
            try:
                if shell:
                    result = subprocess.run(
                        cmd_array[0], 
                        shell=True, 
                        check=True,
                        capture_output=True,
                        text=True
                    )
                else:
                    result = subprocess.run(
                        cmd_array, 
                        check=True,
                        capture_output=True,
                        text=True
                    )
                
                GLib.idle_add(
                    self.label_notify.set_markup,
                    "<span foreground='green'><b>Task completed!</b></span>",
                )
                GLib.timeout_add_seconds(5, lambda: self.label_notify.set_markup("") or False)
                
            except FileNotFoundError as e:
                GLib.idle_add(
                    self.label_notify.set_markup,
                    f"<span foreground='red'><b>Command not found: {cmd_array[0]}</b></span>",
                )
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.strip() if e.stderr else str(e)
                GLib.idle_add(
                    self.label_notify.set_markup,
                    f"<span foreground='red'><b>Error: {error_msg}</b></span>",
                )
        threading.Thread(target=_run, daemon=True).start()


class DialogHandler:
    def __init__(self, dialog, main_notify_label):
        self.dialog = dialog
        self.main_notify_label = main_notify_label

    def on_md_cancel_clicked(self, widget):
        self.dialog.destroy()


class App(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="info.berserkarch.welcome", **kwargs)
        self.window = None

    def do_activate(self):
        if not self.window:
            builder = Gtk.Builder()
            try:
                builder.add_from_file(os.path.join(base_dir, "GUI.glade"))
            except GLib.Error as e:
                print(f"FATAL: Could not load GUI.glade: {e}")
                sys.exit(1)

            handler = Handler(builder)
            builder.connect_signals(handler)
            self.window = builder.get_object("main_window")
            self.window.set_application(self)
            self.window.set_icon_name("berserkarch-app")
            self.window.show_all()


if __name__ == "__main__":
    app = App()
    sys.exit(app.run(sys.argv))

