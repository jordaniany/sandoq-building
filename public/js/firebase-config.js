// =========================================================
// Firebase Initialization & Cloud Firestore Services
// Sandoq Building Fund | المهندس أبو عادل
// =========================================================

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
import { 
  getFirestore, 
  collection, 
  doc, 
  getDocs, 
  setDoc, 
  addDoc, 
  deleteDoc, 
  onSnapshot, 
  query, 
  orderBy, 
  writeBatch 
} from "https://www.gstatic.com/firebasejs/10.9.0/firebase-firestore.js";

export const firebaseConfig = {
  projectId: "sandoq-building-2026",
  appId: "1:899977185298:web:e784ad280b2c6db005f0cb",
  storageBucket: "sandoq-building-2026.firebasestorage.app",
  apiKey: "AIzaSyAfiohpZKcngSCzhuq36hLgblXqi6oK42U",
  authDomain: "sandoq-building-2026.firebaseapp.com",
  messagingSenderId: "899977185298"
};

let app = null;
let db = null;
let isConnected = false;

try {
  app = initializeApp(firebaseConfig);
  db = getFirestore(app);
  isConnected = true;
  console.log("Firebase initialized successfully! 🟢");
} catch (error) {
  console.error("Firebase init error:", error);
  isConnected = false;
}

export { db, isConnected, collection, doc, getDocs, setDoc, addDoc, deleteDoc, onSnapshot, query, orderBy, writeBatch };
