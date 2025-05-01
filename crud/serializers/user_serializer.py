from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

# Import langsung dari model authentication.models
from authentication.models import User


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk menampilkan daftar user (tanpa detail lengkap)
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name','show_password', 'last_name', 'role', 'is_active', 'date_joined',
                  'last_login']
        read_only_fields = ['date_joined', 'last_login']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer untuk operasi CRUD pada model User
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirmation = serializers.CharField(write_only=True, required=True)
    show_password = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password_confirmation',
                  'first_name', 'last_name', 'role', 'is_active', 'is_staff',
                  'show_password', 'date_joined', 'last_login']
        read_only_fields = ['date_joined', 'last_login']

    def validate(self, attrs):
        # Validasi password dan konfirmasi password harus sama
        if 'password' in attrs and 'password_confirmation' in attrs:
            if attrs['password'] != attrs['password_confirmation']:
                raise serializers.ValidationError({
                    "password_confirmation": "Password dan konfirmasi password tidak cocok."
                })

        return attrs

    def create(self, validated_data):
        # Remove password_confirmation dari validated_data
        validated_data.pop('password_confirmation', None)

        # Ambil password dan username
        password = validated_data.pop('password')

        # Buat user dengan data yang tersisa
        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        return user

    def update(self, instance, validated_data):
        # Remove password_confirmation dari validated_data
        validated_data.pop('password_confirmation', None)

        # Jika password ada dalam validated_data, update password
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)

        # Update field lainnya
        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance