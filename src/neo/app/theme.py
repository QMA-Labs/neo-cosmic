ACCENT = "#71E5C1"
ACCENT_2 = "#8AA8FF"
SURFACE = "rgba(15, 20, 31, 218)"
TEXT = "#F4F7FF"
MUTED = "#AAB3C5"

PANEL_STYLE = f"""
QFrame#panel {{ background: {SURFACE};
  border: 1px solid rgba(190,220,255,72); border-radius: 24px; }}
QFrame#glassPanel {{ background: transparent; border: none; }}
QLabel {{ color: {TEXT}; background: transparent; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#elapsed {{ color: #8AF7D8; font-size: 12px; font-weight: 800; }}
QLabel#gpuBadge {{ color: #071713; background: {ACCENT}; border-radius: 10px;
  padding: 5px 9px; font-weight: 800; }}
QLabel#connectionBadge {{ color: #D7E4FF; background: rgba(138,168,255,34);
  border: 1px solid rgba(160,205,255,50); border-radius: 10px; padding: 5px 8px;
  font-size: 10px; font-weight: 800; }}
QLabel#connectionBadge[online="true"] {{ color: #071713; background: #8AF7D8; }}
QLabel#activity {{ color: #AFC5E8; background: rgba(90,120,190,18);
  border-radius: 9px; padding: 6px 9px; font-size: 11px; }}
QLabel#activity[error="true"] {{ color: #FFD1D8; background: rgba(230,80,110,30); }}
QTextBrowser#transcript {{ background: rgba(255,255,255,9); color: {TEXT};
  border: 1px solid rgba(255,255,255,24); border-radius: 17px; padding: 8px; }}
QScrollBar:vertical {{ background: transparent; width: 7px; margin: 8px 1px; }}
QScrollBar::handle:vertical {{ background: rgba(138,168,255,120); border-radius: 3px;
  min-height: 28px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QLineEdit {{ background: rgba(255,255,255,15); color: {TEXT}; border: 1px solid
  rgba(180,220,255,55); border-radius: 18px; padding: 12px 14px; }}
QComboBox#modeSelector {{ background: rgba(138,168,255,24); color: #E8EEFF;
  border: 1px solid rgba(160,205,255,45); border-radius: 11px; padding: 7px 10px; }}
QComboBox#modeSelector QAbstractItemView {{ background: #17223A; color: #F4F7FF;
  selection-background-color: #35536A; }}
QPushButton {{ background: {ACCENT}; color: #0B1715; border: none; border-radius: 13px;
  padding: 10px 15px; font-weight: 700; }}
QPushButton:hover {{ background: #92F3D6; }}
QPushButton#chip {{ background: rgba(138,168,255,28); color: #DCE5FF;
  border: 1px solid rgba(160,205,255,52); border-radius: 12px; padding: 7px 9px; }}
QPushButton#chip:hover {{ background: rgba(113,229,193,55); color: white; }}
QPushButton#controlButton {{ background: rgba(255,255,255,18); color: #DCE8FF;
  border: 1px solid rgba(180,220,255,45); padding: 7px; }}
QProgressBar {{ background: rgba(255,255,255,18); border: none; border-radius: 4px; }}
QProgressBar::chunk {{ background: {ACCENT_2}; border-radius: 4px; }}
"""

LIGHT_PANEL_STYLE = f"""
QFrame#panel {{ background: rgba(242,247,255,232); border: 1px solid rgba(80,115,170,62);
  border-radius: 24px; }}
QFrame#glassPanel {{ background: transparent; border: none; }}
QLabel {{ color: #142033; background: transparent; }}
QLabel#muted {{ color: #59677C; }}
QLabel#elapsed {{ color: #3B62C4; font-size: 12px; font-weight: 800; }}
QLabel#gpuBadge {{ color: #08251F; background: #61DDBA; border-radius: 10px;
  padding: 5px 9px; font-weight: 800; }}
QLabel#connectionBadge {{ color: #2B3E68; background: rgba(92,116,200,22);
  border: 1px solid rgba(80,110,180,38); border-radius: 10px; padding: 5px 8px;
  font-size: 10px; font-weight: 800; }}
QLabel#connectionBadge[online="true"] {{ color: #08251F; background: #61DDBA; }}
QLabel#activity {{ color: #52637F; background: rgba(92,116,200,18);
  border-radius: 9px; padding: 6px 9px; font-size: 11px; }}
QLabel#activity[error="true"] {{ color: #92283C; background: rgba(220,70,90,25); }}
QTextBrowser#transcript {{ background: rgba(255,255,255,130); color: #142033;
  border: 1px solid rgba(70,105,160,35); border-radius: 17px; padding: 8px; }}
QScrollBar:vertical {{ background: transparent; width: 7px; margin: 8px 1px; }}
QScrollBar::handle:vertical {{ background: rgba(76,105,190,100); border-radius: 3px;
  min-height: 28px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QLineEdit {{ background: rgba(255,255,255,155); color: #142033;
  border: 1px solid rgba(70,105,160,50); border-radius: 18px; padding: 12px 14px; }}
QComboBox#modeSelector {{ background: rgba(255,255,255,125); color: #24345C;
  border: 1px solid rgba(80,110,180,42); border-radius: 11px; padding: 7px 10px; }}
QPushButton {{ background: {ACCENT}; color: #08251F; border: none; border-radius: 13px;
  padding: 10px 15px; font-weight: 700; }}
QPushButton:hover {{ background: #7BE7C8; }}
QPushButton#chip {{ background: rgba(92,116,200,25); color: #24345C;
  border: 1px solid rgba(80,110,180,44); border-radius: 12px; padding: 7px 9px; }}
QPushButton#controlButton {{ background: rgba(255,255,255,90); color: #24345C;
  border: 1px solid rgba(80,110,180,40); padding: 7px; }}
QProgressBar {{ background: rgba(30,55,90,18); border: none; border-radius: 4px; }}
QProgressBar::chunk {{ background: #687FEA; border-radius: 4px; }}
"""
