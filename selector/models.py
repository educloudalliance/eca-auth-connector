
import string
from random import choice
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.core import validators
from django.utils import timezone

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.
    Username, password and email are required. Other fields are optional.
    """
    username = models.CharField(_('username'), max_length=2048, unique=True,
        help_text=_('Required. 2048 characters or fewer. Letters, digits and '
                    '@/./+/-/_ only.'),
        validators=[
            validators.RegexValidator(r'^[\w.@+-]+$', _('Enter a valid username.'), 'invalid')
        ])
    first_name = models.CharField(_('first name'), max_length=2048, blank=True)
    last_name = models.CharField(_('last name'), max_length=2048, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def create_register_tokens(self):
        """ Create tokens for user
        Tokens are create based on the information we have for the user.
        Returns a list of all created tokens.
        """
        t = RegisterToken(user=self, method=RegisterToken.EMAIL)
        t.save()
        return [t]

    def send_register_tokens(self):
        for token in self.registertokens.filter(sent=False):
            token.send_token()


class RegisterToken(models.Model):
    EMAIL = 'email'
    METHOD_CHOICES = (
        (EMAIL, _('#method-email')),
    )
    user = models.ForeignKey(User, related_name='registertokens')
    token = models.CharField(max_length=200)
    issued_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=200, choices=METHOD_CHOICES, default=EMAIL)
    sent = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = ''.join([choice(string.letters + string.digits) for i in range(30)])
        return super(RegisterToken, self).save(*args, **kwargs)

    def send_token(self):
        if self.method == RegisterToken.EMAIL:
            self.send_email()

    def send_email(self):
        from django.template.loader import select_template
        template = select_template('registration_email.txt')
        context = {
          'user': self.user,
          'register_token': self.token,
          'issued_at': self.issued_at,
        }
        message = template.render(context)
        from_email = _('#register-email-from-address')
        self.user.email_user(_('#registration-email-subject'), message, from_email)
        self.sent = True
        self.save()


