# Pexels в MemeGenerator

Для режима `images: photos` приложение при наличии ключа сначала
ищет фотографию в Pexels. Если сервис недоступен, возвращает пустую
выдачу или присылает невалидное изображение, пробует Wikimedia Commons,
после чего показывает текстовую карточку. Режимы `commons` и `local`
работают независимо от Pexels.

## Где взять API-ключ

1. Зарегистрируйтесь на [Pexels](https://www.pexels.com/api/).
2. Запросите Pexels API Key на странице API, **когда выдача возобновится**.
   На 22 октября 2026 года Pexels сообщает, что новые ключи временно
   не выдаются. Ранее полученные ключи можно использовать.
3. В корне проекта создайте локальный файл `.env` (он исключён из Git):

   ```dotenv
   MEMEGEN_PEXELS__API_KEY=your-api-key
   ```

4. В GitHub откройте **Settings → Secrets and variables → Actions →
   New repository secret**, задайте имя `MEMEGEN_PEXELS__API_KEY` и
   вставьте туда **значение** API-ключа. Не присылайте его в чат или PR.
5. Для проверки в GitHub Actions используется
   `.github/workflows/photo-search-acceptance.yml`. Секрет передаётся
   через `secrets.MEMEGEN_PEXELS__API_KEY`; без секрета работает Commons.

## Настройки без секретов

```yaml
images: photos
slide_mode: image_with_caption
pexels:
  orientation: landscape
  size: large
  per_page: 15
  timeout_seconds: 15
```

Реквизиты `pexels.api_key` в YAML **запрещены**. Другие параметры
можно менять через `config.yaml` либо переменными среды, например
`MEMEGEN_PEXELS__PER_PAGE=10`.

Для API используется `GET https://api.pexels.com/v1/search`,
передача ключа выполняется **только** заголовком `Authorization`
на API-хост. Прямая загрузка идёт с `images.pexels.com` по HTTPS.
Внешние хосты, редиректы, неверный MIME и слишком большие файлы
отклоняются. Тесты не требуют действующего ключа.

## Атрибуция фотографий

В `result.attribution.json` указаны ссылка на фотографию, её
автор и ссылка на страницу автора. При распространении ролика
размещайте рядом с ним [ссылку на Pexels](https://www.pexels.com/)
и кредит фотографа по [правилам API](https://www.pexels.com/api/documentation/).
Проверяйте лицензию, особенно при коммерческом использовании.

Pexels ранжирует выдачу сам, но пока **не проверяется** соответствие
содержимого изображения смыслу всей ситуации. Для этого потребуется
отдельный этап визуально-текстового ранжирования.
