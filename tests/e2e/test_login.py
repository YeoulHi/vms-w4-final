"""End-to-End Tests for User Authentication

테스트 대상: 사용자 로그인 및 대시보드 접근 흐름

이 테스트는 실제 웹 브라우저를 제어하여 사용자 관점의 전체 흐름을 검증합니다.
Playwright를 사용하여 Chrome/Firefox에서 자동으로 테스트합니다.

실행 방법:
    pytest tests/e2e/test_login.py -v

주의사항:
    - 이 테스트는 localhost에서 Django 개발 서버가 실행 중이어야 합니다.
    - Playwright 브라우저가 설치되어야 합니다: playwright install
    - 테스트 실행 시간: 3~5초 (단위 테스트보다 느림)
"""

import pytest
from playwright.sync_api import Page, expect
from tests.factories import UserFactory


@pytest.mark.django_db
class TestLoginFlow:
    """사용자 로그인 및 인증 관련 E2E 테스트"""

    def test_login_page_loads_successfully(self, page: Page, live_server):
        """로그인 페이지가 올바르게 로드되는지 검증

        시나리오:
        1. 로그인 URL로 이동
        2. 페이지가 정상 로드되고 필수 요소(사용자명, 비밀번호 입력 필드)가 있는지 확인
        """
        # Arrange: 로그인 페이지 URL
        login_url = f"{live_server.url}/login/"

        # Act: 페이지로 이동
        page.goto(login_url)

        # Assert: 페이지 로드 확인
        expect(page).to_have_title("Login")  # 페이지 제목이 "Login"인지 확인

        # 필수 입력 필드가 보이는지 확인
        username_input = page.get_by_label("Username")
        expect(username_input).to_be_visible()

        password_input = page.get_by_label("Password")
        expect(password_input).to_be_visible()

        # 로그인 버튼이 보이는지 확인
        login_button = page.get_by_role("button", name="Login")
        expect(login_button).to_be_visible()

    def test_user_can_login_with_valid_credentials(self, page: Page, live_server):
        """유효한 자격증명(사용자명/비밀번호)으로 로그인 성공

        시나리오:
        1. 테스트 사용자 생성
        2. 로그인 페이지에서 사용자명/비밀번호 입력
        3. 로그인 버튼 클릭
        4. 대시보드 페이지로 리디렉션 확인
        5. 환영 메시지에 사용자명이 표시되는지 확인
        """
        # Arrange: 테스트 사용자 생성 (DB에 저장됨)
        user = UserFactory(username='testuser', password='testpass123')

        # Act: 로그인 페이지로 이동
        login_url = f"{live_server.url}/login/"
        page.goto(login_url)

        # 사용자명 입력 (자동 대기로 입력 필드가 클릭 가능할 때까지 기다림)
        page.get_by_label("Username").fill("testuser")

        # 비밀번호 입력
        page.get_by_label("Password").fill("testpass123")

        # 로그인 버튼 클릭
        page.get_by_role("button", name="Login").click()

        # Assert: 대시보드로 리디렉션되었는지 확인
        dashboard_url = f"{live_server.url}/dashboard/"
        expect(page).to_have_url(dashboard_url)

        # 대시보드 페이지의 콘텐츠 확인
        dashboard_title = page.locator("h1:has-text('Dashboard')")
        expect(dashboard_title).to_be_visible()

        # 환영 메시지에 사용자명이 있는지 확인
        welcome_message = page.locator("text=Welcome, testuser!")
        expect(welcome_message).to_be_visible()

    def test_login_fails_with_invalid_password(self, page: Page, live_server):
        """잘못된 비밀번호로 로그인 실패

        시나리오:
        1. 테스트 사용자 생성 (올바른 비밀번호: testpass123)
        2. 로그인 페이지에서 잘못된 비밀번호 입력
        3. 로그인 시도
        4. 오류 메시지 표시 확인
        5. 로그인 페이지에 남아있는지 확인
        """
        # Arrange
        user = UserFactory(username='testuser', password='testpass123')

        # Act: 로그인 페이지로 이동
        login_url = f"{live_server.url}/login/"
        page.goto(login_url)

        # 사용자명과 잘못된 비밀번호 입력
        page.get_by_label("Username").fill("testuser")
        page.get_by_label("Password").fill("wrongpassword123")

        # 로그인 버튼 클릭
        page.get_by_role("button", name="Login").click()

        # Assert: 오류 메시지가 표시되는지 확인
        error_message = page.locator("text=didn't match")
        expect(error_message).to_be_visible()

        # 로그인 페이지에 여전히 있는지 확인 (대시보드로 이동하지 않음)
        expect(page).to_have_url(login_url)

    def test_unauthenticated_user_cannot_access_dashboard(self, page: Page, live_server):
        """인증되지 않은 사용자가 대시보드에 직접 접근 시 로그인 페이지로 리디렉션

        시나리오:
        1. 로그인하지 않은 상태에서 대시보드 URL로 직접 이동
        2. 로그인 페이지로 자동 리디렉션되는지 확인
        """
        # Act: 로그인하지 않고 대시보드 URL로 직접 이동
        dashboard_url = f"{live_server.url}/dashboard/"
        page.goto(dashboard_url)

        # Assert: 로그인 페이지로 리디렉션되었는지 확인
        login_url = f"{live_server.url}/login/"
        expect(page).to_have_url(login_url)
