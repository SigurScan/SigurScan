package ro.sigurscan.app

import android.Manifest
import android.app.Application
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import android.provider.OpenableColumns
import android.content.SharedPreferences
import android.text.Html
import android.util.Base64
import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.content.ContextCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.serialization.Serializable
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Request
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.File
import java.io.ByteArrayOutputStream
import java.io.FileOutputStream
import java.io.IOException
import java.net.SocketTimeoutException
import java.net.URI
import java.net.UnknownHostException
import java.net.URLDecoder
import java.security.MessageDigest
import java.nio.charset.StandardCharsets
import java.util.*
import java.util.concurrent.TimeUnit
import java.util.regex.Pattern
import javax.net.ssl.SSLException
import kotlin.math.roundToInt
import kotlin.math.max
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlin.coroutines.suspendCoroutine
import retrofit2.HttpException

// Domain logic extracted from the ScannerViewModel God object into cohesive extension
// functions. Behaviour is identical; the ViewModel keeps the observable state, while
// these functions operate on it. prefs/gson/api are module-internal on the ViewModel.

internal fun ScannerViewModel.loadTriageState() {
    val json = prefs.getString("triage_steps_state", null)
    if (json == null) return

    val type = object : TypeToken<Map<String, List<Int>>>() {}.type
    val values: Map<String, List<Int>> = gson.fromJson(json, type)
    triageStepProgress = values.mapValues { it.value.toSet() }
}

internal fun ScannerViewModel.saveTriageState() {
    val serializable = triageStepProgress.mapValues { it.value.toList() }
    val type = object : TypeToken<Map<String, List<Int>>>() {}.type
    prefs.edit().putString("triage_steps_state", gson.toJson(serializable, type)).apply()
}

fun ScannerViewModel.isTriageStepDone(category: String, index: Int): Boolean {
    return triageStepProgress[category]?.contains(index) == true
}

fun ScannerViewModel.setTriageStep(category: String, index: Int, done: Boolean) {
    val current = triageStepProgress[category]?.toMutableSet() ?: mutableSetOf()
    if (done) current.add(index) else current.remove(index)
    triageStepProgress = triageStepProgress.toMutableMap().apply { this[category] = current }
    saveTriageState()
}

internal fun ScannerViewModel.loadEducationState() {
    val raw = prefs.getString("education_lessons_done", null)
    if (raw == null) return
    val type = object : TypeToken<Set<String>>() {}.type
    completedLessons = gson.fromJson(raw, type)
}

internal fun ScannerViewModel.saveEducationState() {
    val type = object : TypeToken<Set<String>>() {}.type
    prefs.edit().putString("education_lessons_done", gson.toJson(completedLessons, type)).apply()
}

fun ScannerViewModel.setLessonCompleted(lessonId: String, completed: Boolean = true) {
    completedLessons = if (completed) {
        completedLessons + lessonId
    } else {
        completedLessons - lessonId
    }
    saveEducationState()
}
