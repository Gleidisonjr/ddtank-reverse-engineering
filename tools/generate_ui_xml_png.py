"""
Generates the PickGliss UI core.xml asset package (xml.png) for DDTank.
In 7Road DDTank, xml.png is not a static image file, but an FZip archive containing
core.xml and related PickGliss UI styling definitions parsed by ComponentFactory.
"""

import os
import zipfile
import io

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WWW_DIR = os.path.join(BASE_DIR, 'www')

CORE_XML_CONTENT = '''<?xml version="1.0" encoding="utf-8" ?>
<style>
    <!-- PickGliss Core Typography & Fonts -->
    <custom classname="flash.text.TextFormat" stylename="defaultFont" font="Arial" size="12" color="0xFFFFFF" />
    <custom classname="flash.text.TextFormat" stylename="defaultFontBold" font="Arial" size="12" color="0xFFFFFF" bold="true" />
    <custom classname="flash.text.TextFormat" stylename="defaultFontYellow" font="Arial" size="12" color="0xFFE800" />
    
    <!-- Core PickGliss Alerts -->
    <custom classname="com.pickgliss.ui.controls.alert.SimpleAlert" stylename="SimpleAlert" frameMiniW="300" frameMiniH="180" />
    <custom classname="com.pickgliss.ui.controls.alert.SimpleAlert" stylename="TimeoutAlert" frameMiniW="300" frameMiniH="180" />
    
    <!-- Choicefigure / Character Registration Fallback Styles -->
    <custom classname="flash.text.TextFormat" stylename="choicefigure.StyleNickname" font="Arial" size="12" color="0xFFFFFF" />
    <custom classname="flash.text.TextFormat" stylename="choicefigure.StyleNicknameUnvaialabel" font="Arial" size="12" color="0xFF0000" />
    
    <components>
        <!-- Standard Windows & Frames -->
        <component classname="com.pickgliss.ui.controls.Frame" stylename="core.Frame" backStyle="core.FrameBack" closestyle="core.CloseBtn" titleStyle="core.FrameTitle" />
        <component classname="com.pickgliss.ui.controls.BaseButton" stylename="core.CloseBtn" />
        <component classname="com.pickgliss.ui.text.FilterFrameText" stylename="core.FrameTitle" textFormatStyle="defaultFont" />
        <component classname="com.pickgliss.ui.controls.TextButton" stylename="core.SimpleButton" textStyle="defaultFont" />
    </components>
    
    <bitmaps>
    </bitmaps>
</style>
'''

def create_ui_xml_package():
    # Build ZIP package in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('core.xml', CORE_XML_CONTENT.encode('utf-8'))
    zip_bytes = buf.getvalue()

    # Destination directories
    targets = [
        os.path.join(WWW_DIR, 'flash', 'ui', 'xml', 'xml.png'),
        os.path.join(WWW_DIR, 'ui', 'xml', 'xml.png'),
    ]

    for target in targets:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, 'wb') as f:
            f.write(zip_bytes)
        print(f"[+] Successfully wrote PickGliss UI package ({len(zip_bytes)} bytes) -> {target}")

if __name__ == '__main__':
    create_ui_xml_package()
