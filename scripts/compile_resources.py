from PySide6.QtCore import QResource
import os

def compile_resources():
    # Create a temporary resource file with the logos
    with open('quantumops/resources.qrc', 'w') as f:
        f.write('''<!DOCTYPE RCC>
<RCC version="1.0">
    <qresource prefix="/">
        <file>images/projectflow_logo.png</file>
        <file>images/rosievision_logo.png</file>
    </qresource>
</RCC>''')

    # Create images directory if it doesn't exist
    os.makedirs('quantumops/images', exist_ok=True)

    # Create placeholder logos
    with open('quantumops/images/projectflow_logo.png', 'wb') as f:
        f.write(b'')  # Empty file for now
    with open('quantumops/images/rosievision_logo.png', 'wb') as f:
        f.write(b'')  # Empty file for now

    # Compile resources
    QResource.registerResource('quantumops/resources.qrc')

if __name__ == '__main__':
    compile_resources() 