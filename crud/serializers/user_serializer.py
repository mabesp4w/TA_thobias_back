# crud/serializers/user_serializer
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
        fields = ['id', 'username', 'email', 'first_name', 'show_password', 'last_name', 'role', 'is_active',
                  'date_joined',
                  'last_login']
        read_only_fields = ['date_joined', 'last_login']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer untuk operasi CRUD pada model User
    """
    password = serializers.CharField(
        write_only=True,
        required=False,  # <- bikin opsional
        allow_blank=True  # <- boleh string kosong saat update
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True
    )
    show_password = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password_confirmation',
            'first_name', 'last_name', 'role', 'is_active', 'is_staff',
            'show_password', 'date_joined', 'last_login'
        ]
        extra_kwargs = {
            'username': {'required': False},  # ini berpengaruh karena field model
            'date_joined': {'read_only': True},
            'last_login': {'read_only': True},
        }

    def validate_email(self, value):
        """
        Validasi agar email harus unik
        """
        if value:  # Hanya validasi jika email diisi
            # Check untuk create (instance belum ada)
            if not self.instance and User.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email ini sudah digunakan oleh user lain.")

            # Check untuk update (instance sudah ada)
            if self.instance and User.objects.filter(email=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Email ini sudah digunakan oleh user lain.")

        return value

    def validate_username(self, value):
        """
        Validasi agar username harus unik (opsional karena biasanya sudah unique di model)
        """
        # Check untuk create (instance belum ada)
        if not self.instance and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username ini sudah digunakan oleh user lain.")

        # Check untuk update (instance sudah ada)
        if self.instance and User.objects.filter(username=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Username ini sudah digunakan oleh user lain.")

        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirmation = attrs.get('password_confirmation')

        # Validasi hanya jika password diisi
        if password or password_confirmation:
            if password != password_confirmation:
                raise serializers.ValidationError({
                    "password_confirmation": "Password dan konfirmasi password tidak cocok."
                })

        # Validasi email tidak boleh kosong jika field diberikan
        if 'email' in attrs and not attrs['email']:
            raise serializers.ValidationError({
                "email": "Email tidak boleh kosong."
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

        # Kalau ada key password, tapi kosong → abaikan
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        # Update field lain
        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance