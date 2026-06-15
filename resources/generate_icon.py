import os, sys
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)

p = QPixmap(256, 256)
p.fill(Qt.transparent)
pt = QPainter(p)
pt.setBrush(QColor(99, 102, 241))
pt.setPen(Qt.NoPen)
pt.drawRoundedRect(32, 32, 192, 192, 48, 48)
pt.end()
p.save('D:/Projects/DeepSeekMonitor/resources/icon.png')
print('Icon saved successfully')
app.quit()
