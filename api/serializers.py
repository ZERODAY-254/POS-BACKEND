from rest_framework import serializers

from .models import ApprovalRequest, Branch, OfflineSyncLog, Terminal


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class TerminalSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Terminal
        fields = '__all__'


class ApprovalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRequest
        fields = '__all__'


class OfflineSyncLogSerializer(serializers.ModelSerializer):
    terminal_name = serializers.CharField(source='terminal.name', read_only=True)

    class Meta:
        model = OfflineSyncLog
        fields = '__all__'
