"""Factory Boy - Test Data Generation

이 파일은 테스트 데이터를 일관되게 생성하는 팩토리를 정의합니다.
각 팩토리는 모델의 필수 필드를 설정하고, Faker를 사용해 자동으로 값을 생성합니다.

Usage:
    from tests.factories import UserFactory, MetricRecordFactory

    # 1명의 사용자 생성
    user = UserFactory()

    # 3명의 사용자 생성
    users = UserFactory.create_batch(3)

    # 특정 값으로 사용자 생성
    admin_user = UserFactory(username='admin', is_staff=True)
"""

import factory
from django.contrib.auth.models import User
from apps.ingest.models import MetricRecord


class UserFactory(factory.django.DjangoModelFactory):
    """테스트용 사용자 생성 팩토리

    Example:
        user = UserFactory()  # 자동 생성
        user = UserFactory(username='john', email='john@example.com')  # 커스텀
    """

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """비밀번호 설정 (post_generation으로 set_password 메서드 호출)

        Args:
            extracted: 명시적으로 전달된 비밀번호 ('testpass123' 등)
                      생략 시 기본값 'defaultpass123' 사용
        """
        password = extracted or 'defaultpass123'
        obj.set_password(password)
        if create:
            obj.save()


class MetricRecordFactory(factory.django.DjangoModelFactory):
    """테스트용 성과 지표 레코드 생성

    Example:
        metric = MetricRecordFactory()  # 랜덤 데이터로 생성
        metrics = MetricRecordFactory.create_batch(5, year=2024)  # 5개 생성, year는 2024로 지정
    """

    class Meta:
        model = MetricRecord

    year = factory.Faker('year', min_value=2020, max_value=2025)
    department = factory.Faker('word')  # 실제로는 선택지 제한 필요
    metric_type = factory.Faker('word')
    metric_value = factory.Faker(
        'pydecimal',
        left_digits=5,
        right_digits=2,
        positive=True,
        allow_infinity=False,
        allow_nan=False
    )

    # unique_together 제약 때문에 필요한 경우가 있으므로
    # 명시적으로 값을 설정할 수 있도록 함
