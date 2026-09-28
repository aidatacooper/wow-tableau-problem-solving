"""使用官方 tableauserverclient (TSC) 发布工作簿到 Tableau Cloud (cooperwh 站点)"""

from pathlib import Path
import argparse
import sys
import tableauserverclient as TSC

sys.stdout.reconfigure(encoding='utf-8')

import os

SERVER_URL = os.getenv("TABLEAU_SERVER_URL", "https://10ax.online.tableau.com")
SITE_ID = os.getenv("TABLEAU_SITE_ID", "cooperwh")
TOKEN_NAME = os.getenv("TABLEAU_TOKEN_NAME", "cooperwh")
TOKEN_SECRET = os.getenv("TABLEAU_TOKEN_SECRET", "")



def publish_workbook(twbx_path: Path, workbook_name: str = None, project_name: str = "default"):
    twbx_path = Path(twbx_path).resolve()
    if not twbx_path.is_file():
        raise FileNotFoundError(f"文件不存在: {twbx_path}")

    workbook_name = workbook_name or twbx_path.stem

    # 1. 认证
    auth = TSC.PersonalAccessTokenAuth(TOKEN_NAME, TOKEN_SECRET, site_id=SITE_ID)
    server = TSC.Server(SERVER_URL, use_server_version=True)

    with server.auth.sign_in(auth):
        print(f"[OK] TSC 登录成功 (API 版本: {server.version}, 站点: {SITE_ID})")

        # 2. 定位目标项目
        all_projects, _ = server.projects.get()
        target_project = next((p for p in all_projects if p.name == project_name), None)
        if not target_project:
            # 如果不存在，自动创建或使用 default
            target_project = next(p for p in all_projects if p.name == "default")
        print(f"[OK] 目标项目: {target_project.name} (ID: {target_project.id})")

        # 3. 创建并发布工作簿
        wb_item = TSC.WorkbookItem(name=workbook_name, project_id=target_project.id)
        published_wb = server.workbooks.publish(
            wb_item,
            str(twbx_path),
            mode=TSC.Server.PublishMode.Overwrite
        )

        print("\n=== [SUCCESS] 工作簿已通过 TSC 成功发布到 Tableau Cloud! ===")
        print(f"工作簿名称 : {published_wb.name}")
        print(f"工作簿 ID   : {published_wb.id}")
        print(f"在线访问 URL: {published_wb.webpage_url}")
        
        # 4. 获取视图列表
        server.workbooks.populate_views(published_wb)
        print(f"包含视图数 : {len(published_wb.views)}")
        for view in published_wb.views:
            print(f" - 视图: {view.name} | URL: {view.content_url}")

        return published_wb


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用 tableauserverclient 上传工作簿到 Tableau Cloud")
    parser.add_argument("file", help="TWBX 文件路径")
    parser.add_argument("--name", help="发布后的工作簿名称", default=None)
    parser.add_argument("--project", help="目标项目名称（默认: default）", default="default")
    args = parser.parse_args()

    publish_workbook(args.file, args.name, args.project)
