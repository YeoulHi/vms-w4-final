"""Global Pytest Fixtures

이 파일은 전역 Fixture를 정의합니다.
Fixture는 테스트에 필요한 설정, 데이터, 클라이언트 등을 제공하는 함수입니다.

Usage:
    def test_something(authenticated_user):
        # authenticated_user 객체가 자동으로 주입됨
        assert authenticated_user.is_active
"""

import pytest
from django.test import Client
from tests.factories import UserFactory


@pytest.fixture
def authenticated_user(db):
    """인증된 테스트 사용자 반환

    Returns:
        User: username='testuser', password='testpass123'인 활성 사용자

    Example:
        def test_user_profile(authenticated_user):
            assert authenticated_user.username == 'testuser'
    """
    user = UserFactory(username='testuser', password='testpass123')
    return user


@pytest.fixture
def authenticated_client(db, authenticated_user):
    """로그인된 Django 테스트 클라이언트 반환

    이 Fixture는 자동으로 authenticated_user에 로그인한 상태의 클라이언트를 제공합니다.
    HTTP 요청을 시뮬레이션할 때 사용합니다.

    Returns:
        Client: 로그인된 테스트 클라이언트

    Example:
        def test_dashboard_access(authenticated_client):
            response = authenticated_client.get('/dashboard/')
            assert response.status_code == 200
    """
    client = Client()
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def sample_users(db):
    """여러 테스트 사용자 생성

    Returns:
        list: 5명의 테스트 사용자 리스트

    Example:
        def test_user_list(sample_users):
            assert len(sample_users) == 5
    """
    return UserFactory.create_batch(5)
