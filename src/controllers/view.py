from __future__ import annotations

class ViewController:
    MIN_ZOOM = 80
    MAX_ZOOM = 200
    ZOOM_STEP = 10

    def __init__(self, app) -> None:
        self.app = app

    def apply_view_settings(self) -> None:
        self._apply_view_state(
            zoom=self.app.view_zoom,
            status_bar=self.app.status_var.get(),
            focus=self.app.focus_var.get(),
            theme=None,
        )

    def toggle_wrap(self) -> None:
        self.app.text.config(wrap="word" if self.app.wrap_var.get() else "none")
        self._refresh_toolbar()

    def toggle_statusbar(self) -> None:
        enabled = bool(self.app.status_var.get())
        if enabled:
            if hasattr(self.app, "statusbar"):
                self.app.statusbar.show()
                self.app.statusbar.render()
        else:
            if hasattr(self.app, "statusbar"):
                self.app.statusbar.hide()
        self.app.set_view_prefs(status_bar=enabled)
        self._refresh_toolbar()

    def _render_statusbar(self) -> None:
        if hasattr(self.app, "statusbar"):
            self.app.statusbar.schedule_render()

    def _update_statusbar(self) -> None:
        self._render_statusbar()

    def zoom_in(self) -> None:
        self._adjust_zoom(self.ZOOM_STEP)

    def zoom_out(self) -> None:
        self._adjust_zoom(-self.ZOOM_STEP)

    def zoom_reset(self) -> None:
        self._apply_zoom(self._default_zoom())

    def reset_view(self) -> None:
        self._apply_view_state(
            theme="warm",
            zoom=self._default_zoom(),
            status_bar=True,
            focus=False,
        )

    def toggle_focus_mode(self) -> None:
        enabled = bool(self.app.focus_var.get())
        self._apply_focus_mode(enabled)
        self.app.set_view_prefs(focus=enabled)
        if self.app.status_var.get():
            self._render_statusbar()

    def _apply_view_state(
        self,
        *,
        theme: str | None,
        zoom: int | None,
        status_bar: bool | None,
        focus: bool | None,
    ) -> None:
        if theme:
            self.app.set_theme(theme)
        if zoom is not None:
            self._apply_zoom(zoom)
        if status_bar is not None:
            self.app.status_var.set(bool(status_bar))
            self.toggle_statusbar()
        if focus is not None:
            self.app.focus_var.set(bool(focus))
            self._apply_focus_mode(bool(focus))
            self.app.set_view_prefs(focus=bool(focus))

    def _apply_focus_mode(self, enabled: bool) -> None:
        if not hasattr(self.app, "toolbar") or not hasattr(self.app, "sidebar"):
            return
        if enabled:
            self.app.toolbar.frame.grid_remove()
            self.app.sidebar.frame.grid_remove()
        else:
            self.app.toolbar.frame.grid()
            self.app.sidebar.frame.grid()
        if hasattr(self.app, "menubar") and self.app.menubar:
            if hasattr(self.app.menubar, "set_focus_mode"):
                self.app.menubar.set_focus_mode(enabled)
        self._refresh_toolbar()

    def _refresh_toolbar(self) -> None:
        toolbar = getattr(self.app, "toolbar", None)
        if toolbar and hasattr(toolbar, "refresh_states"):
            try:
                toolbar.refresh_states()
            except Exception:
                pass

    def _adjust_zoom(self, delta: int) -> None:
        current = int(getattr(self.app, "view_zoom", self._default_zoom()))
        self._apply_zoom(current + delta)

    def _apply_zoom(self, zoom: int) -> None:
        if not self.app.text_font:
            return
        base = self._base_font_size()
        zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, int(zoom)))
        size = max(8, int(round(base * (zoom / 100))))
        self.app.text_font.configure(size=size)
        if hasattr(self.app, "_update_format_tags"):
            self.app._update_format_tags()
        self.app.view_zoom = zoom
        self.app.set_view_prefs(zoom=zoom)
        if self.app.status_var.get():
            self._render_statusbar()

    def _base_font_size(self) -> int:
        if getattr(self.app, "base_font_size", 0):
            return int(self.app.base_font_size)
        try:
            return int(self.app.text_font.cget("size"))
        except (AttributeError, ValueError):
            return 12

    def _default_zoom(self) -> int:
        return 100
