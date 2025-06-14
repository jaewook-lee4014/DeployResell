#!/usr/bin/env python3
"""
배포 도우미 스크립트
Streamlit Community Cloud 배포를 위한 준비 작업을 수행합니다.
"""

import os
import subprocess
import sys

def check_requirements():
    """requirements.txt 파일 확인"""
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt 파일이 없습니다.")
        return False
    
    print("✅ requirements.txt 파일 확인됨")
    return True

def check_data_files():
    """데이터 파일 확인"""
    data_files = ['data/results.xlsx', 'data/search_info.xlsx']
    missing_files = []
    
    for file in data_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️  다음 데이터 파일이 없습니다: {', '.join(missing_files)}")
        print("   크롤러를 먼저 실행하여 데이터를 생성하세요: python main.py")
        return False
    
    print("✅ 데이터 파일 확인됨")
    return True

def check_git():
    """Git 저장소 확인"""
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
        print("✅ Git 설치 확인됨")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git이 설치되지 않았습니다.")
        return False

def init_git_repo():
    """Git 저장소 초기화"""
    try:
        # Git 저장소 초기화
        subprocess.run(['git', 'init'], check=True)
        print("✅ Git 저장소 초기화됨")
        
        # .gitignore 확인
        if not os.path.exists('.gitignore'):
            print("⚠️  .gitignore 파일이 없습니다.")
        
        # 파일 추가
        subprocess.run(['git', 'add', '.'], check=True)
        print("✅ 파일 추가됨")
        
        # 커밋
        subprocess.run(['git', 'commit', '-m', 'Initial commit for deployment'], check=True)
        print("✅ 초기 커밋 완료")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 작업 실패: {e}")
        return False

def main():
    print("🚀 Streamlit Community Cloud 배포 준비")
    print("=" * 50)
    
    # 현재 디렉토리 확인
    if not os.path.exists('dashboard.py'):
        print("❌ dashboard.py 파일을 찾을 수 없습니다.")
        print("   맘이베베_개선버전 디렉토리에서 실행하세요.")
        sys.exit(1)
    
    # 체크리스트 실행
    checks = [
        check_requirements(),
        check_data_files(),
        check_git()
    ]
    
    if not all(checks):
        print("\n❌ 배포 준비가 완료되지 않았습니다.")
        sys.exit(1)
    
    print("\n📋 배포 준비 완료!")
    print("\n다음 단계:")
    print("1. GitHub에 새 저장소 생성")
    print("2. 다음 명령어 실행:")
    print("   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git")
    print("   git branch -M main")
    print("   git push -u origin main")
    print("3. https://share.streamlit.io 에서 배포")
    print("   - Repository: YOUR_USERNAME/YOUR_REPO_NAME")
    print("   - Branch: main")
    print("   - Main file path: dashboard.py")
    
    # Git 저장소 초기화 여부 확인
    if not os.path.exists('.git'):
        response = input("\nGit 저장소를 초기화하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            init_git_repo()

if __name__ == "__main__":
    main() 