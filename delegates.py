"""
Custom delegates for table widgets.
"""

import json
from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QTextDocument

class DetailsDelegate(QStyledItemDelegate):
    """Custom delegate for formatting the details column"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paint(self, painter, option, index):
        if index.column() == 2:  # details column
            # Get the text
            text = index.data(Qt.DisplayRole)
            
            # Create a document for HTML rendering
            doc = QTextDocument()
            doc.setHtml(text)
            
            # Save painter state
            painter.save()
            
            # Set up the painter
            painter.translate(option.rect.topLeft())
            painter.setClipRect(option.rect.translated(-option.rect.topLeft()))
            
            # Draw the document
            doc.drawContents(painter)
            
            # Restore painter state
            painter.restore()
        else:
            # Use default painting for other columns
            super().paint(painter, option, index)
            
    def sizeHint(self, option, index):
        if index.column() == 2:  # details column
            # Create a document for HTML rendering
            doc = QTextDocument()
            doc.setHtml(index.data(Qt.DisplayRole))
            
            # Return the size of the document
            return QSize(doc.idealWidth(), doc.size().height())
        return super().sizeHint(option, index)

def format_details(details):
    """Format the details into a visually appealing HTML string"""
    try:
        # Try to parse as JSON
        data = json.loads(details)
        
        # Start with a container div
        html = '<div style="font-family: monospace; padding: 5px;">'
        
        # Format based on data type
        if isinstance(data, dict):
            html += '<div>{</div>'
            for key, value in data.items():
                html += f'<div style="margin-left: 20px;">'
                html += f'"{key}": '
                if isinstance(value, (dict, list)):
                    html += format_details(json.dumps(value))
                else:
                    html += f'{json.dumps(value)}'
                html += '</div>'
            html += '<div>}</div>'
        elif isinstance(data, list):
            html += '<div>[</div>'
            for item in data:
                html += '<div style="margin-left: 20px;">'
                if isinstance(item, (dict, list)):
                    html += format_details(json.dumps(item))
                else:
                    html += f'{json.dumps(item)}'
                html += '</div>'
            html += '<div>]</div>'
        else:
            html += f'{json.dumps(data)}'
            
        html += '</div>'
        return html
    except json.JSONDecodeError:
        # If not JSON, return formatted plain text
        return f'<div style="font-family: monospace; padding: 5px;">{details}</div>' 