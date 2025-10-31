"""Unit Tests for Chart Adapter

테스트 대상: apps/dashboard/utils/chart_adapter.py의 format_chart_data() 함수

이 테스트는 format_chart_data() 함수의 정확성을 검증합니다.
각 테스트는 함수의 특정 동작 시나리오를 다룹니다.

실행 방법:
    pytest tests/unit/test_chart_adapter.py -v
"""

import pytest
from decimal import Decimal
from apps.dashboard.utils.chart_adapter import format_chart_data


class TestChartAdapter:
    """format_chart_data() 함수의 단위 테스트"""

    def test_format_chart_data_with_valid_records(self):
        """정상 데이터를 받았을 때 올바른 Chart.js 형식으로 변환"""
        # Arrange: 테스트 데이터 준비
        records = [
            {'department': 'Computer Science', 'metric_value': Decimal('85.50')},
            {'department': 'Philosophy', 'metric_value': Decimal('62.10')},
        ]

        # Act: 테스트할 함수 실행
        result = format_chart_data(records)

        # Assert: 결과 검증
        # 1. 구조 검증
        assert 'labels' in result, "결과에 'labels' 키가 있어야 함"
        assert 'data' in result, "결과에 'data' 키가 있어야 함"

        # 2. 데이터 개수 검증
        assert len(result['labels']) == 2, "2개의 부서 정보가 있어야 함"
        assert len(result['data']) == 2, "2개의 수치 정보가 있어야 함"

        # 3. 실제 데이터 값 검증
        assert result['labels'][0] == 'Computer Science'
        assert result['labels'][1] == 'Philosophy'
        assert float(result['data'][0]) == 85.5
        assert float(result['data'][1]) == 62.1

    def test_format_chart_data_with_empty_list(self):
        """빈 리스트를 받았을 때 빈 결과 반환"""
        # Arrange
        records = []

        # Act
        result = format_chart_data(records)

        # Assert
        assert result == {"labels": [], "data": []}, "빈 리스트에 대해 빈 딕셔너리 반환"

    def test_format_chart_data_with_missing_department_field(self):
        """'department' 필드가 누락되었을 때 'N/A'를 기본값으로 사용"""
        # Arrange
        records = [
            {'metric_value': Decimal('100')},  # 'department' 필드 누락
        ]

        # Act
        result = format_chart_data(records)

        # Assert
        assert result['labels'][0] == 'N/A', "누락된 부서명은 'N/A'로 채워져야 함"
        assert float(result['data'][0]) == 100.0

    def test_format_chart_data_with_missing_metric_value_field(self):
        """'metric_value' 필드가 누락되었을 때 0을 기본값으로 사용"""
        # Arrange
        records = [
            {'department': 'Engineering'},  # 'metric_value' 필드 누락
        ]

        # Act
        result = format_chart_data(records)

        # Assert
        assert result['labels'][0] == 'Engineering'
        assert result['data'][0] == 0.0, "누락된 수치는 0으로 채워져야 함"

    def test_format_chart_data_converts_decimal_to_float(self):
        """Decimal 타입을 float으로 변환"""
        # Arrange
        records = [
            {'department': 'CS', 'metric_value': Decimal('99.99')},
        ]

        # Act
        result = format_chart_data(records)

        # Assert
        assert isinstance(result['data'][0], float), "데이터는 float 타입이어야 함"
        assert result['data'][0] == 99.99

    def test_format_chart_data_with_large_dataset(self):
        """많은 레코드를 받았을 때도 올바르게 처리"""
        # Arrange
        records = [
            {'department': f'Dept_{i}', 'metric_value': Decimal(str(i * 10))}
            for i in range(1, 11)  # 10개 부서
        ]

        # Act
        result = format_chart_data(records)

        # Assert
        assert len(result['labels']) == 10
        assert len(result['data']) == 10
        assert result['labels'][0] == 'Dept_1'
        assert result['data'][0] == 10.0  # 1 * 10
        assert result['labels'][9] == 'Dept_10'
        assert result['data'][9] == 100.0  # 10 * 10
